"""
YouTube API wrapper for searching and downloading music.
Uses youtube-dl for downloading and processing audio files.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import yt_dlp
import json
import re


class YouTubeAPI:
    def __init__(self, output_path: str = "downloads"):
        """Initialize YouTube API wrapper.
        
        Args:
            output_path: Directory to save downloaded files
        """
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }

    def clean_filename(self, filename: str) -> str:
        """Clean filename to be safe for filesystem.
        
        Args:
            filename: Original filename
            
        Returns:
            Cleaned filename
        """
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Remove or replace other problematic characters
        filename = filename.replace('&', 'and')
        filename = filename.strip()
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict]:
        """Search for YouTube videos.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of video information dictionaries
        """
        try:
            search_opts = {
                **self.ydl_opts,
                'extract_flat': True,
                'quiet': True,
                'no_warnings': True,
                'playlistend': limit + offset
            }
            
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                # Perform search
                results = ydl.extract_info(
                    f"ytsearch{limit + offset}:{query}",
                    download=False
                )
                
                if not results or 'entries' not in results:
                    return []
                
                # Process results
                videos = []
                for entry in results['entries'][offset:]:
                    if entry:
                        videos.append({
                            'title': entry.get('title', ''),
                            'url': entry.get('url', ''),
                            'duration': entry.get('duration', 0),
                            'id': entry.get('id', '')
                        })
                
                return videos
                
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return []

    def download(self, url: str, output_dir: Optional[str] = None) -> Optional[str]:
        """Download a YouTube video as MP3.
        
        Args:
            url: YouTube video URL
            output_dir: Optional custom output directory
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Configure download options
            if output_dir:
                download_opts = {
                    **self.ydl_opts,
                    'outtmpl': os.path.join(
                        output_dir,
                        '%(title)s.%(ext)s'
                    )
                }
            else:
                download_opts = {
                    **self.ydl_opts,
                    'outtmpl': str(self.output_path / '%(title)s.%(ext)s')
                }
            
            # Download and convert to MP3
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    # Clean filename
                    filename = self.clean_filename(info['title'])
                    if output_dir:
                        output_path = os.path.join(output_dir, f"{filename}.mp3")
                    else:
                        output_path = str(self.output_path / f"{filename}.mp3")
                    
                    # Verify file exists
                    if os.path.exists(output_path):
                        return output_path
                        
            return None
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def search_and_download(self, query: str, limit: int = 1) -> List[str]:
        """Search for videos and download them.
        
        Args:
            query: Search query string
            limit: Maximum number of videos to download
            
        Returns:
            List of paths to downloaded files
        """
        # Search for videos
        videos = self.search(query, limit=limit)
        if not videos:
            return []
            
        # Download each video
        downloaded_files = []
        for video in videos[:limit]:
            if file_path := self.download(video['url']):
                downloaded_files.append(file_path)
                
        return downloaded_files
