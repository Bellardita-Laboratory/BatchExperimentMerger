
from moviepy.editor import VideoFileClip, CompositeVideoClip
import os
from multiprocessing import Pool
from tqdm import tqdm

# Change these to choose where to load and save the data
batch_folder_path = r'D:\Stxbp1\Pre_surgery\Corridor\MU_Cx\bad' # Path to the folder containing the experiment folders
output_folder = r'D:\Stxbp1\Pre_surgery\Corridor\MU_Cx\output' # Folder to save the merged videos

# Change these to match the naming convention of the videos
video_extension = '.avi' # The file extension of the videos
split_char = '_' # The character used to split the file name
mouse_number_id = 'Mouse' # The string that identifies the mouse number. Format: Mouse1, Mouse2, etc.
run_number_id = 'Run' # The string that identifies the run number. Format: Run1, Run2, etc.
right_id = 'Right' # The string that identifies the right sided video
left_id = 'Left' # The string that identifies the left sided video
sideview_id = 'VENTRALVIEW' # The string that identifies the sideview video
ventral_id = 'SIDEVIEW' # The string that identifies the ventral video

def merge_videos_top_bottom(video1, video2, output, fps=30, speed_factor=0.1,
                            top_margin=50, middle_margin=50, bottom_margin=50, left_margin=30, right_margin=30):
    # Load video clips
    clip1 = VideoFileClip(video1)
    clip2 = VideoFileClip(video2)

    # Ensure both clips have the same width by resizing them to match the target width
    target_width = clip1.w + right_margin + left_margin  # Final width (adjust as necessary)
    
    final_height = clip1.h + clip2.h + top_margin + middle_margin + bottom_margin

    # Create a composite video where one clip is on top and the other is at the bottom
    final_clip = CompositeVideoClip([
        # Clip 1 at the top
        clip1.set_position(("center", top_margin)),  
        # Clip 2 below the first
        clip2.set_position(("center", clip1.h + top_margin + middle_margin))                    
    ], size=(target_width, final_height))  # Final size is based on width and combined height
    
    final_clip = final_clip.set_fps(fps)
    final_clip = final_clip.speedx(factor=speed_factor)
    
    # Write the result to a file
    final_clip.write_videofile(output, codec="libx264", verbose=False, logger=None)

def retrieve_videos():
    # Get all .avi files in the batch_folder_path
    avi_files = [os.path.join(root, file)
                 for root, dirs, files in os.walk(batch_folder_path)
                 for file in files if file.endswith(video_extension)]
    return avi_files

def get_dictionaried_videos(avi_files):
    # Dictionary to store videos by mouse number and run number
    videos_dict = {}

    for avi_file in avi_files:
        # Extract mouse number and run number from the file name
        base_name = os.path.basename(avi_file)
        parts = base_name.split(split_char)

        mouse_numbers = [part for part in parts if mouse_number_id in part]

        if len(mouse_numbers) == 0:
            print(f'\nSkipping {base_name}: No mouse number found.')
            continue
        mouse_number = mouse_numbers[0]

        run_number = [part.replace(video_extension, '') for part in parts if run_number_id in part]
        if len(run_number) == 0:
            print(f'\nSkipping {base_name}: No run number found.')
            continue
        run_number = run_number[0]

        # If the video is from the right side, add it to the right side of the dictionary
        if right_id in base_name:
            run_number += '_right'
        elif left_id in base_name:
            run_number += '_left'

        if mouse_number not in videos_dict:
            videos_dict[mouse_number] = {}
        
        if run_number not in videos_dict[mouse_number]:
            videos_dict[mouse_number][run_number] = []

        videos_dict[mouse_number][run_number].append(avi_file)
    
    
    
    print('\nOrganization found:')
    for key in videos_dict.keys():
        print(f'Mouse {key}:')
        for run in videos_dict[key]:
            print(f'    Run {run}')
            print(f'        {[os.path.basename(vid) for vid in videos_dict[key][run]]}')
        print('-' * 20)

    return videos_dict

def batch_merge(videos_dict):
    p = Pool()
    
    print('\nMerging videos...')

    args_list = [(mouse_number, run_number, videos_dict[mouse_number][run_number]) for mouse_number in videos_dict for run_number in videos_dict[mouse_number] 
                 if videos_dict[mouse_number][run_number] is not None and videos_dict[mouse_number] is not None]
    n_args = len(args_list)

    for _ in tqdm(p.imap_unordered(func=multiprocess_merge, iterable=args_list), total=n_args):
        pass

    # for _ in tqdm(map(multiprocess_merge, args_list)):
    #     pass

    p.close()
    p.join()

def multiprocess_merge(data):
    mouse_number, run_number, videos = data

    if videos is None:
        return

    sv = None
    vv = None
    for video in videos:
        if sideview_id in video:
            sv = video
        if ventral_id in video:
            vv = video

    if sideview_id is None:
        sv = next(video for video in videos if video != vv)
    if ventral_id is None:
        vv = next(video for video in videos if video != sv)

    if len(videos) == 2 and sv is not None and vv is not None:
        output = os.path.join(output_folder, f'{mouse_number}_{run_number}.mp4')
        
        if os.path.exists(output):
            print(f'\nSkipping {mouse_number} {run_number}: {output} already exists.')
            return
        
        # print(f'\nMerging {sv} and {vv} into {output}')
        merge_videos_top_bottom(vv, sv, output)
    else:
        print(f'\nSkipping {mouse_number} {run_number}: {len(videos)} videos found - {sv} and {vv}')

if __name__ == '__main__':
    # Retrieve all the videos in the batch_folder_path
    avi_files = retrieve_videos()

    print(f'Found {len(avi_files)} videos.')

    # Dictionary to store videos by mouse number and run number
    videos_dict = get_dictionaried_videos(avi_files)

    # Check if videos_dict is None or empty
    if not videos_dict:
        print("No videos found to process. Exiting.")
        exit()

    # Ask the user if they want to continue
    user_input = input("Do you want to continue with the merging process? (Y/n): ").strip().lower()
    if user_input not in ['y', '']:
        print("Process aborted by the user.")
        exit()
    
    if sideview_id == '' and ventral_id == '':
        raise ValueError('Both sideview_id and ventral_id are empty. Please fill at least one of them.')
    
    # Merge videos
    batch_merge(videos_dict)

    print('\nDone!')