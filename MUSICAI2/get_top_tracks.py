"""
Script to download top tracks for each genre.
Uses YouTube API to search and download songs.
"""

import os
import json
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from youtube import YouTubeAPI

# Configuration
DATASETS_DIR = "F:/datasets"  # Base directory for raw audio files
MAX_WORKERS = 4  # Number of parallel downloads
BATCH_SIZE = 50  # Number of songs to download in each batch

def load_genres() -> Dict:
    """Load genre configuration from JSON."""
    with open("src/data/genres.json", "r") as f:
        return json.load(f)["genres"]

def create_genre_dirs(genres: Dict):
    """Create directories for each genre."""
    for genre in genres:
        genre_dir = Path(DATASETS_DIR) / genre
        genre_dir.mkdir(parents=True, exist_ok=True)

def download_track(youtube: YouTubeAPI, query: str, output_dir: str) -> bool:
    """Download a single track.
    
    Args:
        youtube: YouTube API instance
        query: Search query
        output_dir: Output directory
        
    Returns:
        True if successful
    """
    try:
        # Search for the track
        results = youtube.search(query, limit=1)
        if not results:
            print(f"No results found for: {query}")
            return False
            
        # Download the first result
        video = results[0]
        if youtube.download(video["url"], output_dir=output_dir):
            print(f"Downloaded: {video['title']}")
            return True
            
        return False
        
    except Exception as e:
        print(f"Error downloading {query}: {e}")
        return False

def download_genre_tracks(
    youtube: YouTubeAPI,
    genre: str,
    search_terms: List[str],
    count: int
):
    """Download tracks for a specific genre.
    
    Args:
        youtube: YouTube API instance
        genre: Genre name
        search_terms: List of search terms
        count: Number of tracks to download
    """
    output_dir = str(Path(DATASETS_DIR) / genre)
    tracks_per_term = count // len(search_terms)
    
    print(f"\nDownloading {count} tracks for genre: {genre}")
    
    for term in search_terms:
        print(f"\nSearching for: {term}")
        downloaded = 0
        batch = 0
        
        while downloaded < tracks_per_term:
            # Calculate batch size
            remaining = tracks_per_term - downloaded
            current_batch = min(BATCH_SIZE, remaining)
            
            print(f"\nBatch {batch + 1}: Downloading {current_batch} tracks...")
            
            # Search for tracks
            results = youtube.search(
                term,
                limit=current_batch,
                offset=batch * BATCH_SIZE
            )
            
            if not results:
                print("No more results found")
                break
                
            # Download tracks in parallel
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = []
                for video in results:
                    future = executor.submit(
                        youtube.download,
                        video["url"],
                        output_dir=output_dir
                    )
                    futures.append(future)
                
                # Wait for downloads to complete
                for future in futures:
                    if future.result():
                        downloaded += 1
                
            batch += 1
            print(f"Downloaded {downloaded}/{tracks_per_term} tracks for term: {term}")

def main():
    """Main function to download all genre tracks."""
    # Load configuration
    genres = load_genres()
    
    # Create directories
    create_genre_dirs(genres)
    
    # Initialize YouTube API
    youtube = YouTubeAPI()
    
    # Download tracks for each genre
    for genre, config in genres.items():
        download_genre_tracks(
            youtube,
            genre,
            config["search_terms"],
            config["count"]
        )

if __name__ == "__main__":
    main()
