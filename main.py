from moviepy.editor import VideoFileClip, CompositeVideoClip
import os
from multiprocessing import Pool
from tqdm import tqdm

# Change these to choose where to load and save the data
batch_folder_path = r'D:\Stxbp1\Pre_surgery\Corridor\MU_Cx\bad' # Path to the folder containing the experiment folders
output_folder = r'D:\Stxbp1\Pre_surgery\Corridor\MU_Cx\output' # Folder to save the merged videos
batch_name = 'WildType' # Name of the batch to be used in the output file names

# Change these to match the naming convention of the videos
input_video_extension = '.avi' # The file extension of the videos
output_video_extension = '.mp4' # The file extension of the output videos
split_char = '_' # The character used to split the file name
mouse_number_id = 'Mouse' # The string that identifies the mouse number. Format: Mouse1, Mouse2, etc.
run_number_id = 'Run' # The string that identifies the run number. Format: Run1, Run2, etc.
right_id = 'Right' # The string that identifies the right sided video
left_id = 'Left' # The string that identifies the left sided video
cage_id = 'Cage' # The string that identifies the cage number. Format: Cage1, Cage2, etc.
sideview_id = 'VENTRALVIEW' # The string that identifies the sideview video
ventral_id = 'SIDEVIEW' # The string that identifies the ventral video


def merge_videos_top_bottom(top_video:os.PathLike, bottom_video:os.PathLike, output_filepath:os.PathLike, 
                            fps:int=30, speed_factor:float=0.1,
                            top_margin:int=50, middle_margin:int=50, bottom_margin:int=50, left_margin:int=30, right_margin:int=30,
                            codec:str='libx264', verbose:bool=False):
    """
        Merges two videos into a single video where one is on top of the other, with the specified borders. 
        The resulting video is saved to the output file, with a specified frame rate and speed factor.

        Args:
            top_video: Path to the video that will be on top.
            bottom_video: Path to the video that will be at the bottom.
            output_filepath: Path to save the merged video.
            fps: Frame rate of the output video.
            speed_factor: Speed factor of the output video.
            top_margin: Margin between the top of the frame and the top of the top_video (in pixels).
            middle_margin: Margin between the bottom of the top_video and the top of the bottom_video (in pixels).
            bottom_margin: Margin between the bottom of the bottom_video and the bottom of the frame (in pixels).
            left_margin: Margin between the left of the widest video and the left of the frame (in pixels).
            right_margin: Margin between the right of the widest videos and the right of the frame (in pixels).
    """
    # Load video clips
    top_clip = VideoFileClip(top_video)
    bottom_clip = VideoFileClip(bottom_video)

    # Calculate the final width and height of the video based on the margins
    final_width = max(top_clip.w, bottom_clip.w) + right_margin + left_margin
    final_height = top_clip.h + bottom_clip.h + top_margin + middle_margin + bottom_margin

    # Create a composite video where one clip is on top and the other is at the bottom
    final_clip = CompositeVideoClip([
        # Clip 1 at the top
        top_clip.set_position(("center", top_margin)),  
        # Clip 2 below the first
        bottom_clip.set_position(("center", top_clip.h + top_margin + middle_margin))                    
    ], size=(final_width, final_height))  # Final size is based on width and combined height
    
    final_clip = final_clip.set_fps(fps)
    final_clip = final_clip.speedx(factor=speed_factor)
    
    # Write the result to a file
    final_clip.write_videofile(output_filepath, codec=codec, verbose=verbose, logger=None)

def retrieve_videos(folder_path:os.PathLike, extension:str) -> list[os.PathLike]:
    """
        Retrieves all the files with extension 'extension' in the 'folder_path' and its subfolders.

        Returns a list with the full path of each file found.
    """
    return [os.path.join(root, file)
                 for root, _, files in os.walk(folder_path)
                 for file in files if file.endswith(extension)]

def get_filepath_dict(filepaths_list:list[os.PathLike], split_char:str, 
                            mouse_number_id:str, run_number_id:str, cage_id:str,
                            right_id:str, left_id:str,
                            right_video_keyword:str='right', left_video_keyword:str='left'):
    """
        Organizes the paths in the 'filepaths_list' into a dictionary where the keys are the mouse number and run number + left/right keyword.

        Args:
            filepaths_list: List of file paths to organize.
            split_char: Character used to split the file names.
            mouse_number_id: String preceding the mouse number in the file name.
            run_number_id: String preceding the run number in the file name.
            right_id: String that identifies the right sided video.
            left_id: String that identifies the left sided video.
            right_video_keyword: Keyword to add to the run number if the video is from the right side.
            left_video_keyword: Keyword to add to the run number if the video is from the left side.
        
        Returns:
            A dictionary where the keys are the mouse number and the values are 
                dictionaries where the keys are the run number + left/right keyword and the values are a list of file paths.
    """
    # # Dictionary to store videos by mouse number, run number, and cage_number
    return_dict : dict[str,dict[str,list[os.PathLike]]] = dict()

    for filepath in filepaths_list:
        ## Separate the file name by the split character
        base_name : str = os.path.basename(filepath)
        splitted_basename = base_name.split(split_char)

        ## Extract mouse number from the file name
        mouse_numbers = [part for part in splitted_basename if mouse_number_id in part]

        # If no mouse number is found, skip the file
        if len(mouse_numbers) == 0:
            print(f'\nSkipping {base_name}: No mouse number found.')
            continue
        # If multiple mouse numbers are found, choose the first one
        elif len(mouse_numbers) > 1:
            print(f'\nMultiple mouse numbers found in {base_name}: {mouse_numbers}. Chosing the first one...')

        mouse_number = mouse_numbers[0]

        ## Extract run number from the file name
        run_number = [part.replace(video_extension, '') for part in splitted_basename if run_number_id in part]

        # If no run number is found, skip the file
        if len(run_number) == 0:
            print(f'\nSkipping {base_name}: No run number found.')
            continue
        # If multiple run numbers are found, choose the first one
        elif len(run_number) > 1:
            print(f'\nMultiple run numbers found in {base_name}: {run_number}. Chosing the first one...')
        
        run_number = run_number[0]

        cage_number = [part.replace(video_extension, '') for part in parts if cage_id in part]
      
        # If the video is from the right/left side, add the right/left video keyword to the run number
        if right_id in base_name:
            run_number += split_char + right_video_keyword + split_char + cage_number[0]
        elif left_id in base_name:
            run_number += split_char + left_video_keyword + split_char + cage_number[0]

        # Add the mouse number entry to the dictionary if it doesn't exist
        if mouse_number not in return_dict:
            return_dict[mouse_number] = dict()
        
        # Add the run number entry to the dictionary if it doesn't exist
        if run_number not in return_dict[mouse_number]:
            return_dict[mouse_number][run_number] = []

        return_dict[mouse_number][run_number].append(filepath)
    
    print('\nOrganization found:')
    for key in return_dict.keys():
        print(f'Mouse {key}:')
        for run in return_dict[key]:
            print(f'    Run {run}')
            print(f'        {[os.path.basename(vid) for vid in return_dict[key][run]]}')
        print('-' * 20)

    return return_dict

def batch_merge_multiprocessing(filepaths_dict:dict[str,dict[str,list[os.PathLike]]], 
                                top_video_id:str, bottom_video_id:str, 
                                split_char:str, output_folder:str, output_video_extension:str, batch_name:str):
    """
        Merges all the videos in the 'filepaths_dict' using multiprocessing.

        Args:
            filepaths_dict: Dictionary with the videos organized by mouse number and run number.
            top_video_id: String that identifies the top video.
            bottom_video_id: String that identifies the bottom video.
            split_char: Character used to split the file names.
            output_folder: Folder to save the merged videos into.
            output_video_extension: File extension of the output videos.
    """
    # List of arguments to pass to the multiprocess_merge function
    args_list = [(mouse_number, run_number, filepaths_dict[mouse_number][run_number]) for mouse_number in filepaths_dict for run_number in filepaths_dict[mouse_number] 
                 if filepaths_dict[mouse_number] is not None and filepaths_dict[mouse_number][run_number] is not None]
    n_args = len(args_list)

    print('\nMerging videos...')

    # Multiprocessing pool to merge the videos
    p = Pool()
    for _ in tqdm(p.imap_unordered(func=lambda data: merge_videos(data, top_video_id, bottom_video_id, split_char, output_folder, output_video_extension, batch_name), iterable=args_list), total=n_args):
        pass

    p.close()
    p.join()

def merge_videos(data:tuple[str,str,list[os.PathLike]], top_video_id:str, bottom_video_id:str, 
                 split_char:str, output_folder:str, output_video_extension:str, batch_name:str):
    """
        Merges the videos in the 'data' tuple.

        Args:
            data: Tuple with the mouse number, run number and list of video paths.
            top_video_id: String that identifies the top video.
            bottom_video_id: String that identifies the bottom video.
            split_char: Character used to split the file names.
            output_folder: Folder to save the merged videos into.
            output_video_extension: File extension of the output videos.
    """
    # Unpack the data tuple
    mouse_number, run_number, videos = data

    # Check that the videos list is not None
    if videos is None:
        return

    # Get the top and bottom videos
    top_vid = None
    bottom_vid = None
    for video in videos:
        if top_video_id in video:
            top_vid = video
        if bottom_video_id in video:
            bottom_vid = video

    if top_video_id is None:
        top_vid = next(video for video in videos if video != bottom_vid)
    if bottom_video_id is None:
        bottom_vid = next(video for video in videos if video != top_vid)

    # Check if the top and bottom videos were found
    if len(videos) == 2 and top_vid is not None and bottom_vid is not None:
        output = os.path.join(output_folder, f'{mouse_number}{split_char}{run_number}.{output_video_extension}')
        
        if os.path.exists(output):
            print(f'\nSkipping {mouse_number} {run_number}: {output} already exists.')
            return
        
        # Merge the videos
        merge_videos_top_bottom(bottom_vid, top_vid, output)
    else:
        print(f'\nSkipping {mouse_number} {run_number}: {len(videos)} videos found - {top_vid} and {bottom_vid}')

if __name__ == '__main__':
    # Retrieve all the videos in the batch_folder_path
    avi_files = retrieve_videos(batch_folder_path, input_video_extension)

    print(f'Found {len(avi_files)} videos.')

    # Dictionary to store videos by mouse number and run number
    videos_dict = get_filepath_dict(avi_files, split_char, mouse_number_id, run_number_id, cage_id, right_id, left_id)

    # Check if videos_dict is None or empty
    if not videos_dict:
        print("No videos found to process. Exiting...")
        exit()

    # Ask the user if they want to continue
    user_input = input("Do you want to continue with the merging process? (Y/n): ").strip().lower()
    if user_input not in ['y', '']:
        print("Process aborted by the user.")
        exit()
    
    # Check if both sideview_id and ventral_id are empty
    if sideview_id == '' and ventral_id == '':
        raise ValueError('Both sideview_id and ventral_id are empty. Please fill at least one of them.')
    
    # Merge videos
    batch_merge_multiprocessing(videos_dict, sideview_id, ventral_id, split_char, output_folder, output_video_extension, batch_name)

    print('\nDone!')
