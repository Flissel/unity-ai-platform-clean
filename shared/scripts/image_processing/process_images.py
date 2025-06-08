#!/usr/bin/env python3
"""
Image Processing Script for n8n Integration

This script performs various image processing operations and can be executed
directly from n8n workflows using the Execute Command node.

Usage:
  python3 process_images.py --input '{"file_path": "image.jpg", "operation": "resize", "options": {"width": 800, "height": 600}}'
  python3 process_images.py --input-file input.json --operation convert
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import base64
import mimetypes
from io import BytesIO

# Add shared libs to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'libs'))
from common import (
    handle_errors, setup_logging, validate_input, safe_json_loads,
    create_success_response, create_error_response, measure_execution_time,
    safe_read_file, safe_write_file
)
from config import get_config

# Setup logging
logger = setup_logging()
config = get_config()


@measure_execution_time
@handle_errors
def process_image(
    file_path: str,
    operation: str = "info",
    output_path: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process images using various operations."""
    
    logger.info(f"Starting image processing: {operation} on {file_path}")
    
    # Validate file exists
    if not os.path.exists(file_path):
        return create_error_response(
            f"File not found: {file_path}",
            "FileNotFoundError",
            {"file_path": file_path}
        )
    
    # Get file info
    file_info = get_image_info(file_path)
    
    options = options or {}
    
    if operation == "info":
        return get_detailed_image_info(file_path, file_info, options)
    elif operation == "resize":
        return resize_image(file_path, file_info, output_path, options)
    elif operation == "crop":
        return crop_image(file_path, file_info, output_path, options)
    elif operation == "rotate":
        return rotate_image(file_path, file_info, output_path, options)
    elif operation == "flip":
        return flip_image(file_path, file_info, output_path, options)
    elif operation == "convert":
        return convert_image_format(file_path, file_info, output_path, options)
    elif operation == "enhance":
        return enhance_image(file_path, file_info, output_path, options)
    elif operation == "filter":
        return apply_image_filter(file_path, file_info, output_path, options)
    elif operation == "watermark":
        return add_image_watermark(file_path, file_info, output_path, options)
    elif operation == "compress":
        return compress_image(file_path, file_info, output_path, options)
    elif operation == "thumbnail":
        return create_thumbnail(file_path, file_info, output_path, options)
    elif operation == "extract_text":
        return extract_text_from_image(file_path, file_info, options)
    elif operation == "detect_objects":
        return detect_objects_in_image(file_path, file_info, options)
    elif operation == "analyze_colors":
        return analyze_image_colors(file_path, file_info, options)
    elif operation == "remove_background":
        return remove_image_background(file_path, file_info, output_path, options)
    elif operation == "batch_process":
        return batch_process_images(file_path, file_info, options)
    else:
        return create_error_response(
            f"Unknown operation: {operation}",
            "ValueError",
            {"available_operations": [
                "info", "resize", "crop", "rotate", "flip", "convert", "enhance", 
                "filter", "watermark", "compress", "thumbnail", "extract_text", 
                "detect_objects", "analyze_colors", "remove_background", "batch_process"
            ]}
        )


def get_image_info(file_path: str) -> Dict[str, Any]:
    """Get basic image information."""
    
    try:
        from PIL import Image
        
        stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        with Image.open(file_path) as img:
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size_bytes": stat.st_size,
                "extension": Path(file_path).suffix.lower(),
                "mime_type": mime_type,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                "modified_time": stat.st_mtime,
                "created_time": stat.st_ctime
            }
    
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "error": str(e)
        }


def get_detailed_image_info(file_path: str, file_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed image information including EXIF data."""
    
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        import exifread
        
        detailed_info = file_info.copy()
        
        # Extract EXIF data using PIL
        with Image.open(file_path) as img:
            exif_data = {}
            
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)
            
            detailed_info["exif_pil"] = exif_data
            
            # Additional image properties
            detailed_info["color_count"] = len(img.getcolors(maxcolors=256*256*256)) if img.mode in ('RGB', 'RGBA') else None
            detailed_info["is_animated"] = getattr(img, 'is_animated', False)
            detailed_info["n_frames"] = getattr(img, 'n_frames', 1)
        
        # Extract EXIF data using exifread for more detailed info
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                exif_detailed = {}
                for tag in tags.keys():
                    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                        exif_detailed[tag] = str(tags[tag])
                detailed_info["exif_detailed"] = exif_detailed
        except Exception as e:
            logger.warning(f"Could not extract detailed EXIF: {e}")
            detailed_info["exif_detailed"] = {}
        
        # Calculate additional metrics
        detailed_info["aspect_ratio"] = detailed_info["width"] / detailed_info["height"]
        detailed_info["megapixels"] = (detailed_info["width"] * detailed_info["height"]) / 1000000
        detailed_info["size_mb"] = detailed_info["size_bytes"] / (1024 * 1024)
        
        return create_success_response(detailed_info, {
            "operation": "info",
            "format": detailed_info.get("format"),
            "exif_fields": len(detailed_info.get("exif_detailed", {}))
        })
    
    except ImportError:
        return create_error_response(
            "Image processing requires Pillow and exifread libraries",
            "ImportError",
            {"required_packages": ["Pillow", "exifread"]}
        )
    except Exception as e:
        logger.error(f"Error getting detailed image info: {e}")
        return create_error_response(
            f"Image info extraction failed: {str(e)}",
            type(e).__name__
        )


def resize_image(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Resize image to specified dimensions."""
    
    try:
        from PIL import Image
        
        # Get resize parameters
        width = options.get("width")
        height = options.get("height")
        maintain_aspect = options.get("maintain_aspect", True)
        resample = options.get("resample", "LANCZOS")
        
        if not width and not height:
            return create_error_response(
                "Either width or height must be specified",
                "ValueError",
                {"provided_options": options}
            )
        
        with Image.open(file_path) as img:
            original_width, original_height = img.size
            
            # Calculate new dimensions
            if maintain_aspect:
                if width and height:
                    # Fit within bounds while maintaining aspect ratio
                    img.thumbnail((width, height), getattr(Image.Resampling, resample, Image.Resampling.LANCZOS))
                    new_width, new_height = img.size
                elif width:
                    # Calculate height based on width
                    aspect_ratio = original_height / original_width
                    new_width = width
                    new_height = int(width * aspect_ratio)
                    img = img.resize((new_width, new_height), getattr(Image.Resampling, resample, Image.Resampling.LANCZOS))
                else:
                    # Calculate width based on height
                    aspect_ratio = original_width / original_height
                    new_width = int(height * aspect_ratio)
                    new_height = height
                    img = img.resize((new_width, new_height), getattr(Image.Resampling, resample, Image.Resampling.LANCZOS))
            else:
                # Stretch to exact dimensions
                new_width = width or original_width
                new_height = height or original_height
                img = img.resize((new_width, new_height), getattr(Image.Resampling, resample, Image.Resampling.LANCZOS))
            
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_resized{ext}"
            
            img.save(output_path, quality=options.get("quality", 95))
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "original_dimensions": {"width": original_width, "height": original_height},
                "new_dimensions": {"width": new_width, "height": new_height},
                "size_change": {
                    "width_change": new_width - original_width,
                    "height_change": new_height - original_height,
                    "scale_factor_x": new_width / original_width,
                    "scale_factor_y": new_height / original_height
                },
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "resize",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Image resizing requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return create_error_response(
            f"Image resize failed: {str(e)}",
            type(e).__name__
        )


def crop_image(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Crop image to specified region."""
    
    try:
        from PIL import Image
        
        # Get crop parameters
        left = options.get("left", 0)
        top = options.get("top", 0)
        right = options.get("right")
        bottom = options.get("bottom")
        width = options.get("width")
        height = options.get("height")
        
        with Image.open(file_path) as img:
            original_width, original_height = img.size
            
            # Calculate crop box
            if width and height:
                right = left + width
                bottom = top + height
            elif not right or not bottom:
                return create_error_response(
                    "Must specify either (right, bottom) or (width, height)",
                    "ValueError",
                    {"provided_options": options}
                )
            
            # Validate crop box
            if left < 0 or top < 0 or right > original_width or bottom > original_height:
                return create_error_response(
                    "Crop box extends beyond image boundaries",
                    "ValueError",
                    {
                        "image_size": {"width": original_width, "height": original_height},
                        "crop_box": {"left": left, "top": top, "right": right, "bottom": bottom}
                    }
                )
            
            # Perform crop
            cropped_img = img.crop((left, top, right, bottom))
            
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_cropped{ext}"
            
            cropped_img.save(output_path, quality=options.get("quality", 95))
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "original_dimensions": {"width": original_width, "height": original_height},
                "cropped_dimensions": {"width": right - left, "height": bottom - top},
                "crop_box": {"left": left, "top": top, "right": right, "bottom": bottom},
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "crop",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Image cropping requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error cropping image: {e}")
        return create_error_response(
            f"Image crop failed: {str(e)}",
            type(e).__name__
        )


def rotate_image(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Rotate image by specified angle."""
    
    try:
        from PIL import Image
        
        angle = options.get("angle", 90)
        expand = options.get("expand", True)
        fill_color = options.get("fill_color", "white")
        
        with Image.open(file_path) as img:
            original_width, original_height = img.size
            
            # Rotate image
            rotated_img = img.rotate(angle, expand=expand, fillcolor=fill_color)
            
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_rotated_{angle}{ext}"
            
            rotated_img.save(output_path, quality=options.get("quality", 95))
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "original_dimensions": {"width": original_width, "height": original_height},
                "rotated_dimensions": {"width": rotated_img.width, "height": rotated_img.height},
                "rotation_angle": angle,
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "rotate",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Image rotation requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error rotating image: {e}")
        return create_error_response(
            f"Image rotation failed: {str(e)}",
            type(e).__name__
        )


def flip_image(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Flip image horizontally or vertically."""
    
    try:
        from PIL import Image
        
        direction = options.get("direction", "horizontal")  # horizontal, vertical, both
        
        with Image.open(file_path) as img:
            if direction == "horizontal":
                flipped_img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif direction == "vertical":
                flipped_img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            elif direction == "both":
                flipped_img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            else:
                return create_error_response(
                    f"Invalid flip direction: {direction}",
                    "ValueError",
                    {"valid_directions": ["horizontal", "vertical", "both"]}
                )
            
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_flipped_{direction}{ext}"
            
            flipped_img.save(output_path, quality=options.get("quality", 95))
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "flip_direction": direction,
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "flip",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Image flipping requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error flipping image: {e}")
        return create_error_response(
            f"Image flip failed: {str(e)}",
            type(e).__name__
        )


def convert_image_format(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Convert image to different format."""
    
    try:
        from PIL import Image
        
        target_format = options.get("format", "JPEG").upper()
        
        with Image.open(file_path) as img:
            # Handle transparency for formats that don't support it
            if target_format in ["JPEG", "BMP"] and img.mode in ["RGBA", "LA"]:
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background
            
            # Determine output path
            if not output_path:
                name = os.path.splitext(file_path)[0]
                ext_map = {
                    "JPEG": ".jpg",
                    "PNG": ".png",
                    "GIF": ".gif",
                    "BMP": ".bmp",
                    "TIFF": ".tiff",
                    "WEBP": ".webp"
                }
                ext = ext_map.get(target_format, ".jpg")
                output_path = f"{name}{ext}"
            
            # Save with format-specific options
            save_kwargs = {"format": target_format}
            
            if target_format == "JPEG":
                save_kwargs["quality"] = options.get("quality", 95)
                save_kwargs["optimize"] = options.get("optimize", True)
            elif target_format == "PNG":
                save_kwargs["optimize"] = options.get("optimize", True)
            elif target_format == "WEBP":
                save_kwargs["quality"] = options.get("quality", 95)
                save_kwargs["method"] = options.get("method", 6)
            
            img.save(output_path, **save_kwargs)
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "original_format": file_info.get("format"),
                "target_format": target_format,
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "compression_ratio": file_info["size_bytes"] / os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "convert",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Image conversion requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error converting image: {e}")
        return create_error_response(
            f"Image conversion failed: {str(e)}",
            type(e).__name__
        )


def enhance_image(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance image with various adjustments."""
    
    try:
        from PIL import Image, ImageEnhance
        
        with Image.open(file_path) as img:
            enhanced_img = img.copy()
            
            enhancements_applied = []
            
            # Brightness
            if "brightness" in options:
                enhancer = ImageEnhance.Brightness(enhanced_img)
                enhanced_img = enhancer.enhance(options["brightness"])
                enhancements_applied.append(f"brightness: {options['brightness']}")
            
            # Contrast
            if "contrast" in options:
                enhancer = ImageEnhance.Contrast(enhanced_img)
                enhanced_img = enhancer.enhance(options["contrast"])
                enhancements_applied.append(f"contrast: {options['contrast']}")
            
            # Color saturation
            if "color" in options:
                enhancer = ImageEnhance.Color(enhanced_img)
                enhanced_img = enhancer.enhance(options["color"])
                enhancements_applied.append(f"color: {options['color']}")
            
            # Sharpness
            if "sharpness" in options:
                enhancer = ImageEnhance.Sharpness(enhanced_img)
                enhanced_img = enhancer.enhance(options["sharpness"])
                enhancements_applied.append(f"sharpness: {options['sharpness']}")
            
            if not enhancements_applied:
                return create_error_response(
                    "No enhancement parameters provided",
                    "ValueError",
                    {"available_enhancements": ["brightness", "contrast", "color", "sharpness"]}
                )
            
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_enhanced{ext}"
            
            enhanced_img.save(output_path, quality=options.get("quality", 95))
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "enhancements_applied": enhancements_applied,
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "enhance",
                "output_created": True,
                "enhancements_count": len(enhancements_applied)
            })
    
    except ImportError:
        return create_error_response(
            "Image enhancement requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error enhancing image: {e}")
        return create_error_response(
            f"Image enhancement failed: {str(e)}",
            type(e).__name__
        )


def apply_image_filter(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Apply filters to image."""
    
    try:
        from PIL import Image, ImageFilter
        
        filter_type = options.get("filter", "blur")
        
        with Image.open(file_path) as img:
            if filter_type == "blur":
                radius = options.get("radius", 2)
                filtered_img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            elif filter_type == "sharpen":
                filtered_img = img.filter(ImageFilter.SHARPEN)
            elif filter_type == "edge_enhance":
                filtered_img = img.filter(ImageFilter.EDGE_ENHANCE)
            elif filter_type == "edge_enhance_more":
                filtered_img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            elif filter_type == "find_edges":
                filtered_img = img.filter(ImageFilter.FIND_EDGES)
            elif filter_type == "emboss":
                filtered_img = img.filter(ImageFilter.EMBOSS)
            elif filter_type == "smooth":
                filtered_img = img.filter(ImageFilter.SMOOTH)
            elif filter_type == "smooth_more":
                filtered_img = img.filter(ImageFilter.SMOOTH_MORE)
            elif filter_type == "detail":
                filtered_img = img.filter(ImageFilter.DETAIL)
            else:
                return create_error_response(
                    f"Unknown filter type: {filter_type}",
                    "ValueError",
                    {"available_filters": [
                        "blur", "sharpen", "edge_enhance", "edge_enhance_more", 
                        "find_edges", "emboss", "smooth", "smooth_more", "detail"
                    ]}
                )
            
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_{filter_type}{ext}"
            
            filtered_img.save(output_path, quality=options.get("quality", 95))
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "filter_applied": filter_type,
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "filter",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Image filtering requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error applying filter: {e}")
        return create_error_response(
            f"Image filter failed: {str(e)}",
            type(e).__name__
        )


def create_thumbnail(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Create thumbnail of image."""
    
    try:
        from PIL import Image
        
        size = options.get("size", [128, 128])
        if isinstance(size, int):
            size = [size, size]
        
        with Image.open(file_path) as img:
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_thumb{ext}"
            
            img.save(output_path, quality=options.get("quality", 95))
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "original_dimensions": {"width": file_info["width"], "height": file_info["height"]},
                "thumbnail_dimensions": {"width": img.width, "height": img.height},
                "max_size": size,
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "compression_ratio": file_info["size_bytes"] / os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "thumbnail",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Thumbnail creation requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error creating thumbnail: {e}")
        return create_error_response(
            f"Thumbnail creation failed: {str(e)}",
            type(e).__name__
        )


def extract_text_from_image(file_path: str, file_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Extract text from image using OCR."""
    
    try:
        import pytesseract
        from PIL import Image
        
        language = options.get("language", "eng")
        config = options.get("config", "")
        
        with Image.open(file_path) as img:
            # Extract text
            text = pytesseract.image_to_string(img, lang=language, config=config)
            
            # Get detailed data
            data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)
            
            # Process words with confidence
            words = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    words.append({
                        "text": data['text'][i],
                        "confidence": int(data['conf'][i]),
                        "left": int(data['left'][i]),
                        "top": int(data['top'][i]),
                        "width": int(data['width'][i]),
                        "height": int(data['height'][i])
                    })
            
            result = {
                "extracted_text": text.strip(),
                "words": words,
                "word_count": len(text.split()),
                "character_count": len(text),
                "language": language,
                "average_confidence": sum(w["confidence"] for w in words) / len(words) if words else 0,
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "extract_text",
                "words_detected": len(words)
            })
    
    except ImportError:
        return create_error_response(
            "Text extraction requires pytesseract and Pillow libraries",
            "ImportError",
            {"required_packages": ["pytesseract", "Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return create_error_response(
            f"Text extraction failed: {str(e)}",
            type(e).__name__
        )


def detect_objects_in_image(file_path: str, file_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Detect objects in image (placeholder for computer vision)."""
    
    # This would require computer vision libraries like OpenCV, YOLO, etc.
    return create_error_response(
        "Object detection not implemented yet",
        "NotImplementedError",
        {"suggested_libraries": ["opencv-python", "ultralytics", "tensorflow", "torch"]}
    )


def analyze_image_colors(file_path: str, file_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze colors in image."""
    
    try:
        from PIL import Image
        import numpy as np
        
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get image data as numpy array
            img_array = np.array(img)
            
            # Calculate color statistics
            mean_color = np.mean(img_array, axis=(0, 1))
            std_color = np.std(img_array, axis=(0, 1))
            
            # Get dominant colors
            pixels = img_array.reshape(-1, 3)
            unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
            
            # Sort by frequency
            sorted_indices = np.argsort(counts)[::-1]
            top_colors = []
            
            for i in range(min(10, len(sorted_indices))):
                color = unique_colors[sorted_indices[i]]
                count = counts[sorted_indices[i]]
                percentage = (count / len(pixels)) * 100
                
                top_colors.append({
                    "rgb": color.tolist(),
                    "hex": "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2]),
                    "count": int(count),
                    "percentage": float(percentage)
                })
            
            result = {
                "color_statistics": {
                    "mean_rgb": mean_color.tolist(),
                    "std_rgb": std_color.tolist(),
                    "total_pixels": len(pixels),
                    "unique_colors": len(unique_colors)
                },
                "dominant_colors": top_colors,
                "color_distribution": {
                    "red_mean": float(mean_color[0]),
                    "green_mean": float(mean_color[1]),
                    "blue_mean": float(mean_color[2])
                }
            }
            
            return create_success_response(result, {
                "operation": "analyze_colors",
                "colors_analyzed": len(unique_colors)
            })
    
    except ImportError:
        return create_error_response(
            "Color analysis requires Pillow and numpy libraries",
            "ImportError",
            {"required_packages": ["Pillow", "numpy"]}
        )
    except Exception as e:
        logger.error(f"Error analyzing colors: {e}")
        return create_error_response(
            f"Color analysis failed: {str(e)}",
            type(e).__name__
        )


def remove_image_background(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Remove background from image (placeholder)."""
    
    # This would require specialized libraries like rembg, backgroundremover, etc.
    return create_error_response(
        "Background removal not implemented yet",
        "NotImplementedError",
        {"suggested_libraries": ["rembg", "backgroundremover", "opencv-python"]}
    )


def compress_image(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Compress image to reduce file size."""
    
    try:
        from PIL import Image
        
        quality = options.get("quality", 85)
        optimize = options.get("optimize", True)
        
        with Image.open(file_path) as img:
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_compressed{ext}"
            
            # Determine format
            format_name = img.format or "JPEG"
            
            save_kwargs = {"optimize": optimize}
            
            if format_name in ["JPEG", "WEBP"]:
                save_kwargs["quality"] = quality
            
            img.save(output_path, format=format_name, **save_kwargs)
            
            original_size = file_info["size_bytes"]
            compressed_size = os.path.getsize(output_path)
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "file_size_before": original_size,
                "file_size_after": compressed_size,
                "size_reduction": original_size - compressed_size,
                "compression_ratio": original_size / compressed_size,
                "size_reduction_percentage": ((original_size - compressed_size) / original_size) * 100,
                "quality_used": quality,
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "compress",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Image compression requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        return create_error_response(
            f"Image compression failed: {str(e)}",
            type(e).__name__
        )


def add_image_watermark(file_path: str, file_info: Dict[str, Any], output_path: Optional[str], options: Dict[str, Any]) -> Dict[str, Any]:
    """Add watermark to image."""
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        watermark_text = options.get("text", "WATERMARK")
        position = options.get("position", "bottom-right")  # top-left, top-right, bottom-left, bottom-right, center
        opacity = options.get("opacity", 128)  # 0-255
        font_size = options.get("font_size", 36)
        color = options.get("color", "white")
        
        with Image.open(file_path) as img:
            # Create watermark
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Try to use a font
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Get text size
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position
            if position == "top-left":
                x, y = 10, 10
            elif position == "top-right":
                x, y = img.width - text_width - 10, 10
            elif position == "bottom-left":
                x, y = 10, img.height - text_height - 10
            elif position == "bottom-right":
                x, y = img.width - text_width - 10, img.height - text_height - 10
            elif position == "center":
                x, y = (img.width - text_width) // 2, (img.height - text_height) // 2
            else:
                x, y = 10, 10
            
            # Draw watermark
            if isinstance(color, str):
                if color == "white":
                    color = (255, 255, 255, opacity)
                elif color == "black":
                    color = (0, 0, 0, opacity)
                else:
                    color = (255, 255, 255, opacity)  # Default to white
            else:
                color = (*color[:3], opacity)
            
            draw.text((x, y), watermark_text, font=font, fill=color)
            
            # Composite watermark onto image
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            watermarked = Image.alpha_composite(img, watermark)
            
            # Convert back to original mode if needed
            if file_info.get("mode") and file_info["mode"] != 'RGBA':
                watermarked = watermarked.convert(file_info["mode"])
            
            # Save result
            if not output_path:
                name, ext = os.path.splitext(file_path)
                output_path = f"{name}_watermarked{ext}"
            
            watermarked.save(output_path, quality=options.get("quality", 95))
            
            result = {
                "input_file": file_path,
                "output_file": output_path,
                "watermark_text": watermark_text,
                "position": position,
                "opacity": opacity,
                "file_size_before": file_info["size_bytes"],
                "file_size_after": os.path.getsize(output_path),
                "options_used": options
            }
            
            return create_success_response(result, {
                "operation": "watermark",
                "output_created": True
            })
    
    except ImportError:
        return create_error_response(
            "Watermarking requires Pillow library",
            "ImportError",
            {"required_packages": ["Pillow"]}
        )
    except Exception as e:
        logger.error(f"Error adding watermark: {e}")
        return create_error_response(
            f"Watermarking failed: {str(e)}",
            type(e).__name__
        )


def batch_process_images(file_path: str, file_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Batch process multiple images in a directory."""
    
    # This is a placeholder for batch processing functionality
    return create_error_response(
        "Batch processing not implemented yet",
        "NotImplementedError",
        {"note": "Use individual operations on each file instead"}
    )


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(
        description="Process images using various operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get image info
  python3 process_images.py --input '{"file_path": "image.jpg", "operation": "info"}'
  
  # Resize image
  python3 process_images.py --input '{"file_path": "image.jpg", "operation": "resize", "options": {"width": 800, "height": 600}}'
  
  # Convert format
  python3 process_images.py --input '{"file_path": "image.png", "operation": "convert", "options": {"format": "JPEG"}}'
  
  # Extract text (OCR)
  python3 process_images.py --input '{"file_path": "scan.png", "operation": "extract_text", "options": {"language": "eng"}}'
"""
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='JSON input data as string')
    input_group.add_argument('--input-file', help='Path to JSON input file')
    
    # Operation options
    parser.add_argument(
        '--operation', 
        default='info',
        choices=[
            'info', 'resize', 'crop', 'rotate', 'flip', 'convert', 'enhance', 
            'filter', 'watermark', 'compress', 'thumbnail', 'extract_text', 
            'detect_objects', 'analyze_colors', 'remove_background', 'batch_process'
        ],
        help='Image processing operation (default: info)'
    )
    
    # Output options
    parser.add_argument('--output-file', help='Path to save output JSON file')
    parser.add_argument('--output-image', help='Path to save processed image')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    try:
        # Parse input data
        if args.input:
            input_data = safe_json_loads(args.input)
        else:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        
        # Validate input structure
        schema = {
            "file_path": {"type": "string", "required": True},
            "operation": {"type": "string", "required": False},
            "output_path": {"type": "string", "required": False},
            "options": {"type": "object", "required": False}
        }
        
        validate_input(input_data, schema)
        
        # Extract parameters
        file_path = input_data["file_path"]
        operation = input_data.get("operation", args.operation)
        output_path = input_data.get("output_path", args.output_image)
        options = input_data.get("options", {})
        
        # Process image
        result = process_image(
            file_path=file_path,
            operation=operation,
            output_path=output_path,
            options=options
        )
        
        # Output result
        output_json = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Results saved to {args.output_file}")
        else:
            print(output_json)
    
    except Exception as e:
        error_result = create_error_response(str(e), type(e).__name__)
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()