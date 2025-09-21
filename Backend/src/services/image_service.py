"""
Image service for sending crop images through the imageSend API.
"""

import os
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

# Configuration for the imageSend API
IMAGE_SEND_API_URL = os.getenv("IMAGE_SEND_API_URL", "https://api.example.com/imageSend")
IMAGE_SEND_API_KEY = os.getenv("IMAGE_SEND_API_KEY", "")
IMAGE_SEND_TIMEOUT = int(os.getenv("IMAGE_SEND_TIMEOUT", "30"))
IMAGE_SEND_ENABLED = os.getenv("IMAGE_SEND_ENABLED", "true").lower() == "true"

# Path to the images directory
IMAGES_DIR = Path(__file__).parent.parent.parent / "images"


def get_crop_image_mapping() -> Dict[str, str]:
    """
    Get mapping of crop names to image file names.
    Handles case variations and naming conventions.
    """
    # Available images from the directory
    available_images = [
        "alfalfa.png", "Barley.png", "Canola.png", "Carrot.png", "Corn.png",
        "Cotton.png", "Lettuce.png", "Oats.png", "Onion.png", "Peanuts.png",
        "Potato.png", "Rice.png", "Sorghum.png", "Soybean.png", "Sunflower.png",
        "Tomato.png", "Wheatspring.png", "Wheatwinter.png"
    ]
    
    # Create mapping with case-insensitive lookup
    mapping = {}
    for image_file in available_images:
        crop_name = image_file.replace(".png", "").lower()
        # Handle special cases
        if crop_name == "wheatspring":
            mapping["wheat spring"] = image_file
            mapping["spring wheat"] = image_file
        elif crop_name == "wheatwinter":
            mapping["wheat winter"] = image_file
            mapping["winter wheat"] = image_file
        else:
            mapping[crop_name] = image_file
    
    return mapping


def get_image_path_for_crop(crop_name: str) -> Optional[Path]:
    """
    Get the full path to the image file for a given crop name.
    
    Args:
        crop_name: Name of the crop
        
    Returns:
        Path to the image file if found, None otherwise
    """
    if not crop_name:
        return None
        
    mapping = get_crop_image_mapping()
    normalized_name = crop_name.lower().strip()
    
    if normalized_name in mapping:
        image_file = mapping[normalized_name]
        image_path = IMAGES_DIR / image_file
        
        if image_path.exists():
            return image_path
        else:
            logger.warning(f"Image file not found: {image_path}")
    else:
        logger.warning(f"No image mapping found for crop: {crop_name}")
    
    return None


def encode_image_to_base64(image_path: Path) -> Optional[str]:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image, None if error
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        logger.error(f"Failed to encode image {image_path}: {str(e)}")
        return None


async def send_images_to_api(
    crop_names: List[str],
    prediction_type: str,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send crop images to the imageSend API in the correct order.
    
    Args:
        crop_names: List of crop names in order (1-5 for short-term, Jan-Dec for long-term)
        prediction_type: "short_term" or "long_term"
        additional_metadata: Optional metadata to include in the request
        
    Returns:
        Response from the imageSend API
    """
    # Check if image sending is enabled
    if not IMAGE_SEND_ENABLED:
        logger.info("Image sending is disabled via configuration")
        return {"success": True, "message": "Image sending disabled", "images_sent": 0}
    
    if not crop_names:
        logger.warning("No crop names provided for image sending")
        return {"success": False, "error": "No crop names provided"}
    
    # Validate prediction type
    if prediction_type not in ["short_term", "long_term"]:
        logger.error(f"Invalid prediction type: {prediction_type}")
        return {"success": False, "error": f"Invalid prediction type: {prediction_type}"}
    
    # Validate crop count based on prediction type
    expected_count = 5 if prediction_type == "short_term" else 12
    if len(crop_names) > expected_count:
        logger.warning(f"Too many crops for {prediction_type}: {len(crop_names)}, truncating to {expected_count}")
        crop_names = crop_names[:expected_count]
    
    # Prepare images
    images_data = []
    missing_images = []
    
    for i, crop_name in enumerate(crop_names):
        image_path = get_image_path_for_crop(crop_name)
        
        if image_path:
            encoded_image = encode_image_to_base64(image_path)
            if encoded_image:
                images_data.append({
                    "order": i + 1,
                    "crop_name": crop_name,
                    "image_data": encoded_image,
                    "image_format": "png",
                    "file_name": image_path.name
                })
            else:
                missing_images.append(crop_name)
        else:
            missing_images.append(crop_name)
    
    if missing_images:
        logger.warning(f"Missing images for crops: {missing_images}")
    
    if not images_data:
        logger.error("No valid images found for any crops")
        return {"success": False, "error": "No valid images found"}
    
    # Prepare API request payload
    payload = {
        "prediction_type": prediction_type,
        "image_count": len(images_data),
        "images": images_data,
        "metadata": {
            "total_crops": len(crop_names),
            "missing_images": missing_images,
            "timestamp": asyncio.get_event_loop().time(),
            **(additional_metadata or {})
        }
    }
    
    # Send to imageSend API
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {IMAGE_SEND_API_KEY}" if IMAGE_SEND_API_KEY else None
            }
            # Remove None values from headers
            headers = {k: v for k, v in headers.items() if v is not None}
            
            logger.info(f"Sending {len(images_data)} images to imageSend API for {prediction_type}")
            
            async with session.post(
                IMAGE_SEND_API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=IMAGE_SEND_TIMEOUT)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully sent images to imageSend API")
                    return {
                        "success": True,
                        "response": result,
                        "images_sent": len(images_data),
                        "missing_images": missing_images
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"imageSend API returned status {response.status}: {error_text}")
                    return {
                        "success": False,
                        "error": f"API returned status {response.status}",
                        "details": error_text
                    }
                    
    except asyncio.TimeoutError:
        logger.error(f"Timeout sending to imageSend API after {IMAGE_SEND_TIMEOUT}s")
        return {"success": False, "error": "Timeout sending to imageSend API"}
    except Exception as e:
        logger.error(f"Error sending to imageSend API: {str(e)}")
        return {"success": False, "error": f"Failed to send to imageSend API: {str(e)}"}


def extract_crop_names_from_short_term(recommendations: List[Dict[str, Any]]) -> List[str]:
    """
    Extract crop names from short-term prediction results in order.
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        List of crop names in ranking order (1-5)
    """
    crop_names = []
    for rec in recommendations[:5]:  # Ensure max 5 crops
        crop_name = rec.get('crop_name')
        if crop_name:
            crop_names.append(crop_name)
    
    return crop_names


def extract_crop_names_from_long_term(monthly_plans: List[Dict[str, Any]]) -> List[str]:
    """
    Extract crop names from long-term prediction results in month order.
    
    Args:
        monthly_plans: List of monthly plan dictionaries
        
    Returns:
        List of crop names in month order (Jan-Dec)
    """
    # Sort by month to ensure correct order
    sorted_plans = sorted(monthly_plans, key=lambda x: x.get('month', 0))
    
    crop_names = []
    for plan in sorted_plans[:12]:  # Ensure max 12 months
        # Try different possible keys for the best crop recommendation
        best_crop = None
        if 'best_crop' in plan and plan['best_crop']:
            best_crop = plan['best_crop']
        elif 'recommendations' in plan and plan['recommendations']:
            best_crop = plan['recommendations'][0]  # Take top recommendation
        
        if best_crop and 'crop_name' in best_crop:
            crop_names.append(best_crop['crop_name'])
        else:
            # If no crop for this month, we could skip or add a placeholder
            # For now, we'll skip months without crops
            pass
    
    return crop_names


async def process_prediction_and_send_images(
    prediction_result: Dict[str, Any],
    prediction_type: str,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process prediction results and automatically send images.
    
    Args:
        prediction_result: Results from prediction pipeline
        prediction_type: "short_term" or "long_term"
        additional_metadata: Optional metadata to include
        
    Returns:
        Result of image sending operation
    """
    try:
        if prediction_type == "short_term":
            recommendations = prediction_result.get('recommendations', [])
            crop_names = extract_crop_names_from_short_term(recommendations)
        elif prediction_type == "long_term":
            # Try different possible keys for monthly plans
            monthly_plans = (
                prediction_result.get('monthly_plans', []) or
                prediction_result.get('rotation_sequence', []) or
                prediction_result.get('recommendations', [])
            )
            crop_names = extract_crop_names_from_long_term(monthly_plans)
        else:
            return {"success": False, "error": f"Unknown prediction type: {prediction_type}"}
        
        if not crop_names:
            logger.warning(f"No crop names extracted from {prediction_type} prediction")
            return {"success": False, "error": "No crops found in prediction results"}
        
        # Add prediction metadata
        metadata = {
            "parcel_id": prediction_result.get('parcel_id'),
            "month": prediction_result.get('month'),
            "generated_at": prediction_result.get('generated_at'),
            **(additional_metadata or {})
        }
        
        # Send images to API
        result = await send_images_to_api(crop_names, prediction_type, metadata)
        
        logger.info(f"Image sending completed for {prediction_type}: {result.get('success', False)}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing prediction and sending images: {str(e)}")
        return {"success": False, "error": f"Processing failed: {str(e)}"}