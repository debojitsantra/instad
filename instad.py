import os
import argparse
import instaloader
from tqdm import tqdm

def download_media(account, limit):
    try:
        loader = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(loader.context, account)
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"The account '{account}' does not exist.")
        return
    except instaloader.exceptions.ConnectionException:
        print("Unable to establish a connection. Please check your internet connection.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    save_path = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(save_path, exist_ok=True)

    count = 0
    with tqdm(total=limit, ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        for post in profile.get_posts():
            if count >= limit:
                break

            try:
                loader.download_post(post, target=save_path)
                count += 1
                pbar.update(1)
            except instaloader.exceptions.InstaloaderException as e:
                print(f"Error downloading post: {post.url}")
                print(e)
                pbar.update(1)  # Skip the failed post

def main():
    parser = argparse.ArgumentParser(description='Instagram media downloader')
    parser.add_argument('account', type=str, help='Instagram account username')
    parser.add_argument('limit', type=int, help='Number of posts to download')

    args = parser.parse_args()

    try:
        download_media(args.account, args.limit)
        print('Download completed successfully.')
    except Exception as e:
        print('An error occurred during the download process.')
        print(e)

if __name__ == '__main__':
    main()
