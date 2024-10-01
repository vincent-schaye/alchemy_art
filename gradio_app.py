import re
import gradio as gr
from story_generator import generate_bedtime_story
from vector_db_operation import retrieve_existing_story_titles, summarize_and_upsert_story
import os

# Import for handling images
from PIL import Image


def create_interface():
    with gr.Blocks() as app:
        gr.Markdown("# Interactive Bedtime Story Generator")

        story_generator_state = gr.State(None)
        user_id = gr.Textbox(label="User ID")

        # State variables for images
        generated_images = gr.State({
            "eye-monster": "images/eye-monster.png",
            "magic-cupcake": "images/magic-cupcake.png",
            "purple-unicorn": "images/purple-unicorn.png"
        })  # Placeholder for testing purposes. When ready it would be called into the parameter of this function above. @ LINH
        image_descriptions = gr.State(
            ["eye-monster", "magic-cupcake", "purple-unicorn"])  # Hard coded placeholder for now. @ LINH

        with gr.Tabs():
            with gr.TabItem("New Story"):
                name = gr.Textbox(label="Main Character's Name")
                place = gr.Textbox(label="Story Setting")
                tone = gr.Textbox(label="Story Tone")
                moral = gr.Textbox(label="Moral of the Story")
                length = gr.Slider(minimum=1, maximum=6, step=1, label="Story Length (minutes)")
                age = gr.Slider(minimum=1, maximum=10, step=1, label="Target Age")
                new_story_btn = gr.Button("Start New Story")

            with gr.TabItem("Continue Story"):
                story_choice = gr.Dropdown(label="Choose a story to continue", choices=[])
                cont_tone = gr.Textbox(label="New Story Tone")
                cont_moral = gr.Textbox(label="New Moral")
                cont_length = gr.Slider(minimum=1, maximum=6, step=1, label="Continuation Length (minutes)")
                continue_btn = gr.Button("Continue Story")

        with gr.Group(visible=False) as story_interface:
            image_display = gr.Gallery(label="Images")  # Gallery to support multiple images
            story_display = gr.Markdown(label="Story")
            choices_container = gr.Group()
            with choices_container:
                choice_buttons = [gr.Button(f"Choice {i + 1}") for i in range(3)]
            custom_choice = gr.Textbox(label="Or enter your own choice")
            submit_custom = gr.Button("Submit Custom Choice")
            end_button = gr.Button("End Story")

        # New: Save and Main Menu buttons
        save_story_btn = gr.Button("Save Story", visible=False)
        main_menu_btn = gr.Button("Back to Main Menu", visible=False)

        def update_end_button(story_complete):
            return gr.update(value="Back to Main Menu" if story_complete else "End Story")

        def update_story_choices(user_id):
            stories = retrieve_existing_story_titles(user_id)
            return gr.Dropdown(choices=[story[0] for story in stories], value=stories[0][0] if stories else None)

        def update_choices(choices):
            updates = []
            for i in range(3):
                if i < len(choices):
                    updates.append(gr.update(value=choices[i], visible=True))
                else:
                    updates.append(gr.update(visible=False))
            return updates

        def handle_choice(choice, story_generator):
            print(f"Debug: handle_choice called with choice: {choice}")
            try:
                if story_generator is None:
                    print("Debug: No active story generator")
                    return {
                        story_display: "No active story. Please start a new story or continue an existing one.",
                        image_display: [],
                        choice_buttons[0]: gr.update(visible=False),
                        choice_buttons[1]: gr.update(visible=False),
                        choice_buttons[2]: gr.update(visible=False),
                        story_generator_state: None,
                        custom_choice: gr.update(value="", visible=False),
                        submit_custom: gr.update(visible=False),
                        save_story_btn: gr.update(visible=False),
                        main_menu_btn: gr.update(visible=False),
                        end_button: gr.update(visible=False)
                    }

                if choice.lower() == 'exit story':
                    print("Debug: User requested to exit story")
                    return {
                        story_display: "Story ended by user request.",
                        image_display: [],
                        choice_buttons[0]: gr.update(visible=False),
                        choice_buttons[1]: gr.update(visible=False),
                        choice_buttons[2]: gr.update(visible=False),
                        story_generator_state: None,
                        custom_choice: gr.update(value=""),  # Clear the input field
                        save_story_btn: gr.update(visible=True),
                        main_menu_btn: gr.update(visible=True),
                        end_button: gr.update(visible=False)
                    }

                print("Debug: Sending choice to generator")
                next_segment = story_generator.send(choice)
                print(f"Debug: Received next segment: {next_segment}")

                if next_segment.get('complete', False):
                    print("Debug: Story completed")
                    images, text, _ = display_story_segment(next_segment, generated_images.value)
                    return {
                        #story_display: next_segment['story'], this shows full story all again at the end
                        #image_display: next_segment['segments'][-1].get('images', []),
                        story_display: next_segment['segments'][-1]['text'],
                        image_display: images,
                        choice_buttons[0]: gr.update(visible=False),
                        choice_buttons[1]: gr.update(visible=False),
                        choice_buttons[2]: gr.update(visible=False),
                        story_generator_state: None,
                        custom_choice: gr.update(value="", visible=False),
                        submit_custom: gr.update(visible=False),
                        save_story_btn: gr.update(visible=True),
                        main_menu_btn: gr.update(visible=True),
                        end_button: gr.update(visible=False)
                    }

                images, text, choices = display_story_segment(next_segment, generated_images.value)
                choice_updates = update_choices(choices)

                return {
                    image_display: images,
                    story_display: text,
                    choice_buttons[0]: choice_updates[0],
                    choice_buttons[1]: choice_updates[1],
                    choice_buttons[2]: choice_updates[2],
                    story_generator_state: story_generator,
                    custom_choice: gr.update(value="", visible=True),
                    submit_custom: gr.update(visible=True),
                    save_story_btn: gr.update(visible=False),
                    main_menu_btn: gr.update(visible=False),
                    end_button: gr.update(visible=True)
                }
            except StopIteration:
                print("Debug: StopIteration caught, ending story")
                return {
                    story_display: "The story has concluded.",
                    image_display: [],
                    choice_buttons[0]: gr.update(visible=False),
                    choice_buttons[1]: gr.update(visible=False),
                    choice_buttons[2]: gr.update(visible=False),
                    story_generator_state: None,
                    custom_choice: gr.update(value=""),  # Clear the input field
                    save_story_btn: gr.update(visible=True),
                    main_menu_btn: gr.update(visible=True)
                }
            except Exception as e:
                print(f"Debug: Unexpected error in handle_choice: {str(e)}")
                return {
                    story_display: f"An error occurred: {str(e)}",
                    image_display: [],
                    choice_buttons[0]: gr.update(visible=False),
                    choice_buttons[1]: gr.update(visible=False),
                    choice_buttons[2]: gr.update(visible=False),
                    story_generator_state: None,
                    custom_choice: gr.update(value="", visible=False),
                    submit_custom: gr.update(visible=False),
                    save_story_btn: gr.update(visible=False),
                    main_menu_btn: gr.update(visible=True),
                    end_button: gr.update(visible=False)
                }

        def start_or_continue_story(user_id, is_new, *args):  # This is what kicks things of.
            try:
                if is_new:
                    name, place, tone, moral, length, age = args
                    story_generator = generate_bedtime_story(user_id, image_descriptions.value, is_continued=False,
                                                             name=name, place=place,
                                                             tone=tone, moral=moral, length=float(length), age=int(age))
                else:
                    story_choice, tone, moral, length = args
                    story_generator = generate_bedtime_story(user_id, image_descriptions.value, is_continued=True,
                                                             story_choice=story_choice,
                                                             tone=tone, moral=moral, length=float(length))

                first_segment = next(story_generator)
                images, text, choices = display_story_segment(first_segment, generated_images.value)
                choice_updates = update_choices(choices)
                return {
                    story_interface: gr.update(visible=True),
                    image_display: images,
                    # story_display: text,  This would display all the story until latest segment
                    story_display: text.split('\n\n')[-1],  # This will display only the last paragraph
                    choice_buttons[0]: choice_updates[0],
                    choice_buttons[1]: choice_updates[1],
                    choice_buttons[2]: choice_updates[2],
                    custom_choice: gr.update(value="", visible=True),
                    submit_custom: gr.update(visible=True),
                    story_generator_state: story_generator,
                    save_story_btn: gr.update(visible=False),
                    main_menu_btn: gr.update(visible=False),
                    end_button: gr.update(visible=True)
                }

            except Exception as e:
                print(f"Debug: Error in start_or_continue_story: {str(e)}")
                return {
                    story_interface: gr.update(visible=True),
                    story_display: f"An error occurred: {str(e)}",
                    image_display: [],
                    choice_buttons[0]: gr.update(visible=False),
                    choice_buttons[1]: gr.update(visible=False),
                    choice_buttons[2]: gr.update(visible=False),
                    custom_choice: gr.update(value="", visible=False),
                    submit_custom: gr.update(visible=False),
                    story_generator_state: None,
                    save_story_btn: gr.update(visible=False),
                    main_menu_btn: gr.update(visible=True)
                }

        def save_story(user_id, story_text, name, place):
            try:
                summarize_and_upsert_story(user_id, name, story_text, place)
                print(f"Story for {name} in {place} has been saved and upserted.")
                return "Story saved successfully!", gr.update(visible=False), gr.update(visible=True)
            except Exception as e:
                print(f"Error saving story: {str(e)}")
                return f"Error saving story: {str(e)}", gr.update(visible=True), gr.update(visible=True)

        def back_to_main_menu():
            return {
                story_interface: gr.update(visible=False),
                save_story_btn: gr.update(visible=False),
                main_menu_btn: gr.update(visible=False)
            }

        def display_story_segment(story_data, generated_images_dict):
            print(f"Debug: display_story_segment called with: {story_data}")
            if not story_data or 'segments' not in story_data or not story_data['segments']:
                print("Debug: No story segments available.")
                return [], "No story segments available.", []

            segment = story_data['segments'][-1]

            # Extract the text between <segment> tags placed in generate_story_part
            text_match = re.search(r'<segment>(.*?)</segment>', segment['text'], re.DOTALL)
            if text_match:
                text = text_match.group(1).strip()
            else:
                text = segment['text']  # Fallback to the entire text if no tags found

            segment_image_descriptions = segment.get('images', [])
            images = [generated_images_dict.get(img, None) for img in segment_image_descriptions]
            choices = story_data.get('choices', [])  # Modified
            # choices = segment.get('choices', []) old.
            return images, text, choices

        user_id.change(update_story_choices, inputs=[user_id], outputs=[story_choice])

        new_story_btn.click(
            start_or_continue_story,
            inputs=[user_id, gr.State(True), name, place, tone, moral, length, age],
            outputs=[story_interface, image_display, story_display] + choice_buttons + [custom_choice, submit_custom,
                                                                                        story_generator_state,
                                                                                        save_story_btn, main_menu_btn,
                                                                                        end_button]
        )

        continue_btn.click(
            start_or_continue_story,
            inputs=[user_id, gr.State(False), story_choice, cont_tone, cont_moral, cont_length],
            outputs=[story_interface, image_display, story_display] + choice_buttons + [custom_choice, submit_custom,
                                                                                        story_generator_state,
                                                                                        save_story_btn, main_menu_btn,
                                                                                        end_button]
        )

        for button in choice_buttons:
            button.click(
                handle_choice,
                inputs=[button, story_generator_state],
                outputs=[image_display, story_display] + choice_buttons + [story_generator_state, custom_choice,
                                                                           submit_custom, save_story_btn, main_menu_btn,
                                                                           end_button]
            )

        submit_custom.click(
            handle_choice,
            inputs=[custom_choice, story_generator_state],
            outputs=[image_display, story_display] + choice_buttons + [story_generator_state, custom_choice,
                                                                       submit_custom, save_story_btn, main_menu_btn,
                                                                       end_button]
        )

        end_button.click(
            lambda: {
                story_interface: gr.update(visible=False),
                image_display: [],
                story_display: "The story has concluded.",
                choice_buttons[0]: gr.update(visible=False),
                choice_buttons[1]: gr.update(visible=False),
                choice_buttons[2]: gr.update(visible=False),
                story_generator_state: None,
                custom_choice: gr.update(value="", visible=False),
                submit_custom: gr.update(visible=False),
                end_button: gr.update(value="Back to Main Menu")
            },
            outputs=[story_interface, image_display, story_display] + choice_buttons + [story_generator_state,
                                                                                        custom_choice, submit_custom,
                                                                                        end_button, save_story_btn,
                                                                                        main_menu_btn]
        )

        save_story_btn.click(
            save_story,
            inputs=[user_id, story_display, name, place],
            outputs=[gr.Textbox(label="Save Status"), save_story_btn, main_menu_btn]
        )

        main_menu_btn.click(
            back_to_main_menu,
            outputs=[story_interface, save_story_btn, main_menu_btn]
        )

    return app


if __name__ == "__main__":
    interface = create_interface()
    interface.launch()
