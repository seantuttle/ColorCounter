import os.path
import argparse
from math import sqrt, inf
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showwarning, askyesno, showinfo
import cv2
import pandas as pd
from winmagic import magic
from alive_progress import alive_bar
from imutils.video import count_frames

Tk().withdraw()


def parse_command_line_args():
    parser = argparse.ArgumentParser(description='Determine the color of each pixel in the given media content')
    parser.add_argument('-v', '--allowvideos', action='store_true', help='Decide if videos should be allowed')
    parser.add_argument('-m', '--matchcolors', action='store_true', help='Decide if you want colors matched exactly')
    parser.add_argument('-p', '--showprogress', action='store_true', help='Decide if you want to show a progress bar')
    args = vars(parser.parse_args())
    return args


def create_colors_df(match_colors):
    if match_colors:
        colors_csv_path = os.path.join(os.path.dirname(__file__), 'assets/colors.csv')
        column_names = ['delete', 'Name', 'Hex', 'R', 'G', 'B']
        colors_df = pd.read_csv(colors_csv_path, names=column_names)
        colors_df.drop(columns='delete', index=0, inplace=True)
        colors_df['RGB'] = None
        for i in colors_df.index:
            colors_df.loc[i, 'RGB'] = f'rgb=({colors_df.at[i, "R"]}, {colors_df.at[i, "G"]}, {colors_df.at[i, "B"]})'
    else:
        colors_df = []

    return colors_df


def initialize_colors_df(colors_df, match_colors):
    if match_colors:
        colors_df['Count'] = 0
    else:
        colors_df.clear()


def get_media_file_path(allow_videos=False):
    stay_in_loop = True
    show_warning = False
    while stay_in_loop:
        if show_warning:
            message = 'Please select an image file.' if not allow_videos else 'Please select an image or video file.'
            showwarning('Incorrect File Type', message)
        else:
            show_warning = True

        title = 'Select Image File' if not allow_videos else 'Select Image or Video File'
        file_path = askopenfilename(title=title)
        if file_path:
            file_type = magic.from_file(file_path, mime=True)

            # expect string of the form '<media_type>/<file_extension>'
            if file_type.split('/')[0] == 'image' or (allow_videos and file_type.split('/')[0] == 'video'):
                is_video = (file_type.split('/')[0] == 'video')
                stay_in_loop = False

    return is_video, file_path


def get_presentation_file_path(media_file_path, match_colors):
    path_parts = os.path.split(media_file_path)
    presentation_file_directories = path_parts[0]
    file_name = '_matched_color_analysis.csv' if match_colors else '_color_analysis.csv'
    presentation_file_name = path_parts[1].split('.')[0] + file_name
    return os.path.join(presentation_file_directories, presentation_file_name)


def perform_analysis(media_file_path, colors_df, is_video, match_colors, show_progress):
    msg = """
            This may take awhile, but it will run in the background.
            A pop-up will appear when the analysis is done.
            Click OK to begin the analysis.
            """
    showinfo('Analysis Started', msg)
    if is_video:
        cap = cv2.VideoCapture(media_file_path)
        num_frames = count_frames(media_file_path)
        frame_width = cap.get(3)
        frame_height = cap.get(4)
        scale = 1
        if frame_width > 100 or frame_height > 100:
            scale = get_scale(100, frame_width, frame_height)
        new_width = int(scale * frame_width)
        new_height = int(scale * frame_height)
        num_pixels = num_frames * new_width * new_height

        if show_progress:
            with alive_bar(num_pixels) as bar:
                for y in analyze_video_with_progress(cap, colors_df, match_colors):
                    bar()
        else:
            analyze_video(cap, colors_df, match_colors)

        cap.release()
    else:
        img = cv2.imread(media_file_path)
        img = resize_image(img, is_video)
        if show_progress:
            with alive_bar(img.shape[0] * img.shape[1]) as bar:
                for y in analyze_image_with_progress(img, colors_df, match_colors):
                    bar()
        else:
            analyze_image(img, colors_df, match_colors)


def analyze_video_with_progress(cap, colors_df, match_colors):
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = resize_image(frame, True)
        analyze_image(frame, colors_df, match_colors)
        yield


def analyze_video(cap, colors_df, match_colors):
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = resize_image(frame, True)
        analyze_image(frame, colors_df, match_colors)


def resize_image(img, is_video):
    height, width = img.shape[0], img.shape[1]
    max_dimension = 100 if is_video else 500

    if height > max_dimension or width > max_dimension:
        scale = max_dimension / height if height > width else max_dimension / width
        return cv2.resize(img, (int(width * scale), int(height * scale)))
    return img


def get_scale(max_dimension, width, height):
    return max_dimension / height if height > width else max_dimension / width

def analyze_image_with_progress(img, colors_df, match_colors):
    height, width = img.shape[0], img.shape[1]

    for x in range(width):
        for y in range(height):
            bgr = img[y, x]
            if match_colors:
                color_index = get_color(bgr[2], bgr[1], bgr[0], colors_df)
                colors_df.loc[color_index, 'Count'] += 1
            else:
                r, g, b = bgr[2], bgr[1], bgr[0]
                hex_string = convert_rgb_to_hex((r, g, b))
                rgb = f'({r}, {g}, {b})'
                count = get_count(rgb, colors_df)
                colors_df += [{'Count': count,
                               'RGB': rgb,
                               'Hex': hex_string}]
            yield


def analyze_image(img, colors_df, match_colors):
    height, width = img.shape[0], img.shape[1]

    for x in range(width):
        for y in range(height):
            bgr = img[y, x]
            if match_colors:
                color_index = get_color(bgr[2], bgr[1], bgr[0], colors_df)
                colors_df.loc[color_index, 'Count'] += 1
            else:
                r, g, b = bgr[2], bgr[1], bgr[0]
                hex_string = convert_rgb_to_hex((r, g, b))
                rgb = f'({r}, {g}, {b})'
                count = get_count(rgb, colors_df)
                colors_df += [{'Count': count,
                               'RGB': rgb,
                               'Hex': hex_string}]


def convert_rgb_to_hex(rgb):
    hex_string = '#'
    for num in rgb:
        intermediate = num / 16
        int_part = intermediate % 16
        frac_part = intermediate % 1

        first_digit = hex(int(int_part))[-1]
        second_digit = hex(int(16 * frac_part))[-1]

        hex_string += first_digit + second_digit

    return hex_string


def get_count(rgb, colors_df):
    for entry in colors_df:
        if entry['RGB'] == rgb:
            count = entry['Count'] + 1
            colors_df.remove(entry)
            return count
    return 1


def get_color(r, g, b, colors_df):
    min_epsilon = inf
    color_match_index = -1
    for index in colors_df.index:
        curr_rgb = [colors_df.at[index, 'R'], colors_df.at[index, 'G'], colors_df.at[index, 'B']]

        r_epsilon = r - curr_rgb[0]
        g_epsilon = g - curr_rgb[1]
        b_epsilon = b - curr_rgb[2]
        epsilon = sqrt(r_epsilon ** 2 + g_epsilon ** 2 + b_epsilon ** 2)

        if epsilon <= min_epsilon:
            min_epsilon = epsilon
            color_match_index = index

    return color_match_index


def present_data(file_path, colors_df, match_colors):
    unsorted_presentation_df = colors_df.loc[colors_df['Count'] > 0] if match_colors else pd.DataFrame(colors_df)
    presentation_df = unsorted_presentation_df.sort_values(by='Count', ascending=False)

    columns = ['Name', 'Count', 'RGB', 'Hex'] if match_colors else ['Count', 'RGB', 'Hex']
    headers = ['Color Name', 'Count', 'RGB Value', 'Hex Code'] if match_colors else ['Count', 'RGB Value', 'Hex Code']

    presentation_df.to_csv(file_path, index=False, columns=columns, header=headers)

    msg = f"""
            Your results were saved in this file: {os.path.basename(file_path)}
            It is located in the same directory as the media file
            """
    showinfo('Analysis Results', msg)


def main_loop():
    args = parse_command_line_args()
    allow_videos, match_colors, show_progress = args['allowvideos'], args['matchcolors'], args['showprogress']
    should_continue = True
    colors_df = create_colors_df(match_colors)
    while should_continue:
        # Beware that analysis of a video file will take a very [ie. VERY] long time
        # and it will be expensive in terms of resources.
        print("HERE")
        is_video, media_file_path = get_media_file_path(allow_videos=allow_videos)
        print("THERE")
        presentation_file_path = get_presentation_file_path(media_file_path, match_colors)
        initialize_colors_df(colors_df, match_colors)

        perform_analysis(media_file_path, colors_df, is_video, match_colors, show_progress)

        present_data(presentation_file_path, colors_df, match_colors)

        msg = 'Would you like to analyze another image or video?' if allow_videos else 'Would you like to analyze another image?'
        should_continue = askyesno('Continue?', msg)


if __name__ == '__main__':
    print("START")
    main_loop()
    print("END")
