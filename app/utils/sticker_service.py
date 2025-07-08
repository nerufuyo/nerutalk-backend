from typing import List, Dict, Optional
from fastapi import HTTPException, status
import requests
import json
from app.core.config import settings


class StickerService:
    """
    Service for managing stickers and GIFs.
    
    Provides functionality to browse, search, and send stickers and GIFs
    from various providers or a custom sticker collection.
    """
    
    def __init__(self):
        """Initialize the sticker service."""
        self.sticker_packs = self._load_default_sticker_packs()
        self.giphy_api_key = getattr(settings, 'giphy_api_key', None)
        self.tenor_api_key = getattr(settings, 'tenor_api_key', None)
    
    def _load_default_sticker_packs(self) -> List[Dict]:
        """
        Load default sticker packs.
        
        Returns:
            List[Dict]: List of default sticker packs
        """
        return [
            {
                "id": "emotions",
                "name": "Emotions",
                "description": "Express your feelings",
                "thumbnail": "/static/stickers/emotions/thumb.png",
                "stickers": [
                    {
                        "id": "happy",
                        "name": "Happy",
                        "url": "/static/stickers/emotions/happy.png",
                        "tags": ["happy", "smile", "joy"]
                    },
                    {
                        "id": "sad",
                        "name": "Sad",
                        "url": "/static/stickers/emotions/sad.png",
                        "tags": ["sad", "cry", "upset"]
                    },
                    {
                        "id": "love",
                        "name": "Love",
                        "url": "/static/stickers/emotions/love.png",
                        "tags": ["love", "heart", "romance"]
                    },
                    {
                        "id": "angry",
                        "name": "Angry",
                        "url": "/static/stickers/emotions/angry.png",
                        "tags": ["angry", "mad", "rage"]
                    },
                    {
                        "id": "laugh",
                        "name": "Laugh",
                        "url": "/static/stickers/emotions/laugh.png",
                        "tags": ["laugh", "funny", "lol"]
                    }
                ]
            },
            {
                "id": "animals",
                "name": "Animals",
                "description": "Cute animal stickers",
                "thumbnail": "/static/stickers/animals/thumb.png",
                "stickers": [
                    {
                        "id": "cat",
                        "name": "Cat",
                        "url": "/static/stickers/animals/cat.png",
                        "tags": ["cat", "cute", "pet"]
                    },
                    {
                        "id": "dog",
                        "name": "Dog",
                        "url": "/static/stickers/animals/dog.png",
                        "tags": ["dog", "cute", "pet"]
                    },
                    {
                        "id": "panda",
                        "name": "Panda",
                        "url": "/static/stickers/animals/panda.png",
                        "tags": ["panda", "cute", "bear"]
                    },
                    {
                        "id": "rabbit",
                        "name": "Rabbit",
                        "url": "/static/stickers/animals/rabbit.png",
                        "tags": ["rabbit", "cute", "bunny"]
                    }
                ]
            },
            {
                "id": "reactions",
                "name": "Reactions",
                "description": "Quick reactions",
                "thumbnail": "/static/stickers/reactions/thumb.png",
                "stickers": [
                    {
                        "id": "thumbs_up",
                        "name": "Thumbs Up",
                        "url": "/static/stickers/reactions/thumbs_up.png",
                        "tags": ["thumbs", "up", "good", "ok"]
                    },
                    {
                        "id": "thumbs_down",
                        "name": "Thumbs Down",
                        "url": "/static/stickers/reactions/thumbs_down.png",
                        "tags": ["thumbs", "down", "bad", "no"]
                    },
                    {
                        "id": "clap",
                        "name": "Clap",
                        "url": "/static/stickers/reactions/clap.png",
                        "tags": ["clap", "applause", "good"]
                    },
                    {
                        "id": "wave",
                        "name": "Wave",
                        "url": "/static/stickers/reactions/wave.png",
                        "tags": ["wave", "hello", "hi", "bye"]
                    }
                ]
            }
        ]
    
    def get_sticker_packs(self) -> List[Dict]:
        """
        Get all available sticker packs.
        
        Returns:
            List[Dict]: List of sticker packs
        """
        return self.sticker_packs
    
    def get_sticker_pack(self, pack_id: str) -> Optional[Dict]:
        """
        Get a specific sticker pack by ID.
        
        Args:
            pack_id (str): Sticker pack ID
            
        Returns:
            Optional[Dict]: Sticker pack or None if not found
        """
        for pack in self.sticker_packs:
            if pack["id"] == pack_id:
                return pack
        return None
    
    def search_stickers(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search stickers by query.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            List[Dict]: List of matching stickers
        """
        results = []
        query_lower = query.lower()
        
        for pack in self.sticker_packs:
            for sticker in pack["stickers"]:
                # Search in sticker name and tags
                if (query_lower in sticker["name"].lower() or
                    any(query_lower in tag.lower() for tag in sticker.get("tags", []))):
                    
                    sticker_result = sticker.copy()
                    sticker_result["pack_id"] = pack["id"]
                    sticker_result["pack_name"] = pack["name"]
                    results.append(sticker_result)
                    
                    if len(results) >= limit:
                        return results
        
        return results
    
    def get_sticker(self, pack_id: str, sticker_id: str) -> Optional[Dict]:
        """
        Get a specific sticker.
        
        Args:
            pack_id (str): Sticker pack ID
            sticker_id (str): Sticker ID
            
        Returns:
            Optional[Dict]: Sticker or None if not found
        """
        pack = self.get_sticker_pack(pack_id)
        if not pack:
            return None
        
        for sticker in pack["stickers"]:
            if sticker["id"] == sticker_id:
                sticker_result = sticker.copy()
                sticker_result["pack_id"] = pack_id
                sticker_result["pack_name"] = pack["name"]
                return sticker_result
        
        return None
    
    async def search_gifs_giphy(self, query: str, limit: int = 20, offset: int = 0) -> Dict:
        """
        Search GIFs using Giphy API.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            offset (int): Offset for pagination
            
        Returns:
            Dict: Giphy API response with GIFs
            
        Raises:
            HTTPException: If API request fails
        """
        if not self.giphy_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Giphy API not configured"
            )
        
        try:
            url = "https://api.giphy.com/v1/gifs/search"
            params = {
                "api_key": self.giphy_api_key,
                "q": query,
                "limit": limit,
                "offset": offset,
                "rating": "g",  # Safe for general audiences
                "lang": "en"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Transform Giphy response to our format
            gifs = []
            for gif in data.get("data", []):
                gifs.append({
                    "id": gif["id"],
                    "title": gif.get("title", ""),
                    "url": gif["images"]["fixed_height"]["url"],
                    "preview_url": gif["images"]["fixed_height_still"]["url"],
                    "width": int(gif["images"]["fixed_height"]["width"]),
                    "height": int(gif["images"]["fixed_height"]["height"]),
                    "source": "giphy"
                })
            
            return {
                "gifs": gifs,
                "total": data.get("pagination", {}).get("total_count", 0),
                "offset": offset,
                "limit": limit
            }
            
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch GIFs from Giphy: {str(e)}"
            )
    
    async def search_gifs_tenor(self, query: str, limit: int = 20, offset: int = 0) -> Dict:
        """
        Search GIFs using Tenor API.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            offset (int): Offset for pagination
            
        Returns:
            Dict: Tenor API response with GIFs
            
        Raises:
            HTTPException: If API request fails
        """
        if not self.tenor_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Tenor API not configured"
            )
        
        try:
            url = "https://tenor.googleapis.com/v2/search"
            params = {
                "key": self.tenor_api_key,
                "q": query,
                "limit": limit,
                "pos": offset,
                "contentfilter": "high",  # Safe content filter
                "media_filter": "gif"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Transform Tenor response to our format
            gifs = []
            for gif in data.get("results", []):
                media = gif.get("media_formats", {})
                gif_format = media.get("gif", {})
                preview_format = media.get("gifpreview", {})
                
                if gif_format:
                    gifs.append({
                        "id": gif["id"],
                        "title": gif.get("content_description", ""),
                        "url": gif_format["url"],
                        "preview_url": preview_format.get("url", gif_format["url"]),
                        "width": gif_format.get("dims", [0, 0])[0],
                        "height": gif_format.get("dims", [0, 0])[1],
                        "source": "tenor"
                    })
            
            return {
                "gifs": gifs,
                "total": len(gifs),  # Tenor doesn't provide total count
                "offset": offset,
                "limit": limit
            }
            
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch GIFs from Tenor: {str(e)}"
            )
    
    async def get_trending_gifs_giphy(self, limit: int = 20, offset: int = 0) -> Dict:
        """
        Get trending GIFs from Giphy.
        
        Args:
            limit (int): Maximum number of results
            offset (int): Offset for pagination
            
        Returns:
            Dict: Trending GIFs from Giphy
        """
        if not self.giphy_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Giphy API not configured"
            )
        
        try:
            url = "https://api.giphy.com/v1/gifs/trending"
            params = {
                "api_key": self.giphy_api_key,
                "limit": limit,
                "offset": offset,
                "rating": "g"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Transform response
            gifs = []
            for gif in data.get("data", []):
                gifs.append({
                    "id": gif["id"],
                    "title": gif.get("title", ""),
                    "url": gif["images"]["fixed_height"]["url"],
                    "preview_url": gif["images"]["fixed_height_still"]["url"],
                    "width": int(gif["images"]["fixed_height"]["width"]),
                    "height": int(gif["images"]["fixed_height"]["height"]),
                    "source": "giphy"
                })
            
            return {
                "gifs": gifs,
                "total": data.get("pagination", {}).get("total_count", 0),
                "offset": offset,
                "limit": limit
            }
            
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch trending GIFs from Giphy: {str(e)}"
            )


# Global sticker service instance
sticker_service = StickerService()
