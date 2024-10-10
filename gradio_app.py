import re
import gradio as gr
from story_generator import generate_bedtime_story
from vector_db_operation import retrieve_existing_story_titles, summarize_and_upsert_story
import audio_generator as ag
#import audio_class

import os
import io   
from TTS.api import TTS 



# Import for handling images
from PIL import Image


def create_interface():
    with gr.Blocks() as app:
        gr.Markdown("# Interactive Bedtime Story Generator")

        story_generator_state = gr.State(None)
        speaker_state = gr.State(None)
        speakers = ag.get_speaker_names()
        user_id = gr.Textbox(label="User ID")

        if not speakers:
            raise ValueError("No speakers available. Please add speaker files to the speaker directory.")
                   
        #audio_gen = audio_class.AudioGenerator()

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
                speaker_dropdown = gr.Dropdown(choices=ag.get_speaker_names(), label="Select Speaker")
                new_story_btn = gr.Button("Start New Story")

            with gr.TabItem("Continue Story"):
                story_choice = gr.Dropdown(label="Choose a story to continue", choices=[])
                cont_tone = gr.Textbox(label="New Story Tone")
                cont_moral = gr.Textbox(label="New Moral")
                cont_length = gr.Slider(minimum=1, maximum=6, step=1, label="Continuation Length (minutes)")
                speaker_dropdown_continue = gr.Dropdown(choices=ag.get_speaker_names(), label="Select Speaker")
                continue_btn = gr.Button("Continue Story")

            ##### Add Speaker Tab #####
#           with gr.TabItem("Add Speaker"):
#               
#               text_input = gr.Textbox(label="Insert name of speaker.")
#
#               with gr.Row():
#                   # Audio intput to record new voice 
#                   audio_input = gr.Audio(sources="microphone", type="filepath", label="Record your voice")
#
#                   save_button = gr.Button("Save Recording") 
#
#
#
#                   save_button.click(ag.save_recording, inputs=[,ag.speaker_dir], outputs=[])
#                   save_button.click(ag.refresh_speaker_list, inputs=[], outputs=speaker_state)


            ######## Audio Tab on Gradio ########
       #   with gr.TabItem("Audio"):
       #       
       #       # Textbox for testing purpouses 
       #       text_input = gr.Textbox(label="Text to generate audio from")

       #       with gr.Row():
       #           # Audio input to record new voice
       #           audio_input = gr.Audio(sources="microphone", type="filepath", label="Record your voice")

       #           # Button to save the recorded audio
       #           save_button = gr.Button("Save Recording")
       #       
       #       # Dropdown for selecting voice saple to replicate from
       #       speaker_dropdown = gr.Dropdown(choices=ag.get_speaker_names(), label="Choose Speaker")

       #       # Button to generate audio
       #       generate_button = gr.Button("Generate Audio")

       #       # Audio output 
       #       audio_output = gr.Audio(label="Generated Audio")

       #       ### Button actions ###
       #       # Save Recording button action
       #       save_button.click(ag.save_recording, inputs=[audio_input], outputs=speaker_dropdown)

       #       # Generate Audio button press action
       #       generate_button.click(ag.generate_audio, inputs=[text_input, speaker_dropdown], outputs=audio_output)

                

        with gr.Group(visible=False) as story_interface:
            image_display = gr.Gallery(label="Images")  # Gallery to support multiple images
            story_display = gr.Markdown(label="Story")
            play_audio = gr.Audio(label="Play audio")
            choices_container = gr.Group()
            with choices_container:
                choice_buttons = [gr.Button(f"Choice {i + 1}") for i in range(3)]
            custom_choice = gr.Textbox(label="Or enter your own choice")
            submit_custom = gr.Button("Submit Custom Choice")
            end_button = gr.Button("End Story")
            # add audio button

        # New: Save and Main Menu buttons
        save_story_btn = gr.Button("Save Story", visible=False)
        main_menu_btn = gr.Button("Back to Main Menu", visible=False)



#        def #play_audio(text):
#            # Use the generate_audio method to get the audio
#            audio = audio_gen.generate_audio(text)
#            return audio

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

#        def generate_story_audio(text, speaker):
#            try:
#                # Use the audio generation module to create audio from text
#                audio_path = ag.generate_story_audio(text, speaker)
#                return audio_path
#            except Exception as e:
#                print(f"Error generating audio: {e}")
#                return None


        ## the following function deals with the different choices 
        def handle_choice(choice, story_generator, speaker):
            print(f"Debug: handle_choice called with choice: {choice}")
            try:
                # when there has been no story generation hide all the buttons
                if story_generator is None:
                    print("Debug: No active story generator")
                    return {
                        story_display: "No active story. Please start a new story or continue an existing one.",
                        image_display: [],
                        #play_audio: gr.update(visible=False),
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
                        #play_audio: gr.update(visible=True),
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

                # part, not the beginning and not the end
                if next_segment.get('complete', False):
                    print("Debug: Story completed")
                    images, text, _ = display_story_segment(next_segment, generated_images.value)
                    
                    audio_temp_file = ag.generate_audio(text,speaker)
                    
                    #audio_gen.generate_audio(text)
                    return {
                        #story_display: next_segment['story'], this shows full story all again at the end
                        #image_display: next_segment['segments'][-1].get('images', []),
                        story_display: next_segment['segments'][-1]['text'],
                        #play_audio: gr.update(visible=True),
                        image_display: images,
                        play_audio: audio_temp_file,
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

                audio_temp_file = ag.generate_audio(text,speaker)

                return {
                    image_display: images,
                    story_display: text,
                    play_audio: audio_temp_file,
                    choice_buttons[0]: choice_updates[0],
                    choice_buttons[1]: choice_updates[1],
                    choice_buttons[2]: choice_updates[2],
                    story_generator_state: story_generator,
                    custom_choice: gr.update(value="", visible=True),
                    submit_custom: gr.update(visible=True),
                    save_story_btn: gr.update(visible=False),
                    main_menu_btn: gr.update(visible=False),
                    end_button: gr.update(visible=True)
                    # add audio button 
                }
            except StopIteration:
                print("Debug: StopIteration caught, ending story")
                return {
                    story_display: "The story has concluded.",
                    #play_audio: gr.update(visible=True),
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
                    #play_audio: gr.update(visible=False),
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
                    # add audio button 
                }

        ############ This is what kicks things of ############
        def start_or_continue_story(user_id, is_new, speaker, *args):  
            try:
                if is_new:
                    name, place, tone, moral, length, age = args
                    story_generator = generate_bedtime_story(user_id, image_descriptions.value, is_continued=False,
                                                             name=name, place=place,
                                                             tone=tone, moral=moral, length=float(length), age=int(age))# add audio button
                else:
                    story_choice, tone, moral, length = args
                    story_generator = generate_bedtime_story(user_id, image_descriptions.value, is_continued=True,
                                                             story_choice=story_choice,
                                                             tone=tone, moral=moral, length=float(length))# add audio button


                if speaker is None: 
                    raise ValueError("Please select a speaker before starting the story.")

                first_segment = next(story_generator)

                # this where the first part of the story will be generated
                # story generation is triggered automatically
                images, text, choices = display_story_segment(first_segment, generated_images.value)
                choice_updates = update_choices(choices)
                
                # path to output-file 
                audio_temp_file = ag.generate_audio(text,speaker)



                return {
                    ### very first instance of the story ###
                    story_interface: gr.update(visible=True),
                    image_display: images,
                    # story_display: text,  This would display all the story until latest segment
                    story_display: text.split('\n\n')[-1],  # This will display only the last paragraph
                    play_audio: audio_temp_file,
                    choice_buttons[0]: choice_updates[0],
                    choice_buttons[1]: choice_updates[1],
                    choice_buttons[2]: choice_updates[2],
                    custom_choice: gr.update(value="", visible=True),
                    submit_custom: gr.update(visible=True),
                    story_generator_state: story_generator,
                    speaker_state: speaker,
                    save_story_btn: gr.update(visible=False),
                    main_menu_btn: gr.update(visible=False),
                    end_button: gr.update(visible=True)
                    # add audio button 
                }

            except Exception as e:
                print(f"Debug: Error in start_or_continue_story: {str(e)}")
                return {
                    story_interface: gr.update(visible=True),
                    story_display: f"An error occurred: {str(e)}",
                    #play_audio: gr.update(visible=False),
                    image_display: [],
                    choice_buttons[0]: gr.update(visible=False),
                    choice_buttons[1]: gr.update(visible=False),
                    choice_buttons[2]: gr.update(visible=False),
                    custom_choice: gr.update(value="", visible=False),
                    submit_custom: gr.update(visible=False),
                    story_generator_state: None,
                    save_story_btn: gr.update(visible=False),
                    main_menu_btn: gr.update(visible=True)
                    # add audio button 
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


        ###################### UI - Button actions  ######################

        
        # TODO: play audio button
        #play_audio.click(
        #   ag.audio_gen,
        #   inputs=[audio_temp_file],
        #   outputs=[gr.Audio("Play audio")]
        #)

        new_story_btn.click(
            start_or_continue_story,
            inputs=[user_id, gr.State(True), speaker_dropdown, name, place, tone, moral, length, age],
            outputs=[story_interface, image_display, story_display, play_audio] + choice_buttons + [custom_choice, submit_custom,
                                                                                        speaker_state,
                                                                                        story_generator_state,
                                                                                        save_story_btn, main_menu_btn,
                                                                                        end_button]
        )

        continue_btn.click(
            start_or_continue_story,
            inputs=[user_id, gr.State(False), speaker_dropdown_continue,story_choice, cont_tone, cont_moral, cont_length],
            outputs=[story_interface, image_display, story_display, play_audio] + choice_buttons + [custom_choice, submit_custom,
                                                                                        speaker_state,
                                                                                        story_generator_state,
                                                                                        save_story_btn, main_menu_btn,
                                                                                        end_button]
        )

        for button in choice_buttons:
            button.click(
                handle_choice,
                inputs=[button, story_generator_state, speaker_state],
                outputs=[image_display, story_display, play_audio] + choice_buttons + [story_generator_state, custom_choice,
                                                                           submit_custom, save_story_btn, 
                                                                           main_menu_btn, end_button]
            )

        submit_custom.click(
            handle_choice,
            inputs=[custom_choice, story_generator_state, speaker_state],
            outputs=[image_display, story_display, play_audio] + choice_buttons + [story_generator_state, custom_choice,
                                                                       submit_custom, #play_audio,  
                                                                       save_story_btn, main_menu_btn,
                                                                       end_button]
        )

        end_button.click(
            lambda: {
                story_interface: gr.update(visible=False),
                image_display: [],
                story_display: "The story has concluded.",
                ##play_audio: gr.Audio(label="Play audio"),
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
                                                                                        #play_audio,
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

#       ##play_audio.click(
#           generate_story_audio, 
#           inputs=[input_text, speaker_dropdown], 
#           outputs=audio_output
#       )

    return app


if __name__ == "__main__":
    interface = create_interface()
    interface.launch()
