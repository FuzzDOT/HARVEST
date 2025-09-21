# Image Sending Feature Documentation

## Overview

The HARVEST backend now includes automatic image sending functionality that sends crop images to an external `imageSend` API whenever predictions are made. This feature automatically selects the appropriate crop images based on prediction results and sends them in the correct order.

## How It Works

### Short-Term Predictions (5 images)

- When a short-term prediction is made, the system gets the top 5 recommended crops
- Images are sent in ranking order (1st most profitable crop, 2nd most profitable, etc.)
- Maximum of 5 images are sent

### Long-Term Predictions (12 images)

- When a long-term annual plan is made, the system gets the best crop for each month
- Images are sent in chronological order (January crop, February crop, etc.)
- Maximum of 12 images are sent (one per month)

## API Endpoints That Trigger Image Sending

The following endpoints automatically send images after generating predictions:

1. **Short-term predictions:**
   - `POST /api/v1/predict/month` - Monthly recommendations
   - `POST /api/v1/predict/location` (when prediction_type="short_term")

2. **Long-term predictions:**
   - `POST /api/v1/plan/annual` - Annual rotation plans
   - `POST /api/v1/predict/location` (when prediction_type="long_term")

3. **Testing:**
   - `POST /api/v1/test/send-images` - Manual testing endpoint

## Configuration

### Environment Variables

Create a `.env` file in the Backend directory with these settings:

```env
# Required: URL endpoint for the imageSend API
IMAGE_SEND_API_URL=https://api.example.com/imageSend

# Optional: API key for authentication (if required by the imageSend service)
IMAGE_SEND_API_KEY=your_api_key_here

# Optional: Timeout in seconds for API requests (default: 30)
IMAGE_SEND_TIMEOUT=30

# Optional: Enable/disable image sending (set to "false" to disable)
IMAGE_SEND_ENABLED=true
```

### Available Crop Images

The system currently supports images for these crops:

- Alfalfa
- Barley
- Canola
- Carrot
- Corn
- Cotton
- Lettuce
- Oats
- Onion
- Peanuts
- Potato
- Rice
- Sorghum
- Soybean
- Sunflower
- Tomato
- Wheat (Spring)
- Wheat (Winter)

Images are located in `Backend/images/` and are automatically matched to crop names (case-insensitive).

## API Request Format

The imageSend API receives requests in this format:

```json
{
  "prediction_type": "short_term", // or "long_term"
  "image_count": 5,
  "images": [
    {
      "order": 1,
      "crop_name": "Corn",
      "image_data": "base64_encoded_image_data",
      "image_format": "png",
      "file_name": "Corn.png"
    },
    // ... more images
  ],
  "metadata": {
    "total_crops": 5,
    "missing_images": [],
    "timestamp": 1234567890,
    "parcel_id": "P1",
    "month": 9
    // ... additional metadata
  }
}
```

## Response Handling

### Successful Response

When image sending succeeds, the prediction response includes:

```json
{
  // ... normal prediction response fields
  "image_send_result": {
    "success": true,
    "response": {
      // Response from imageSend API
    },
    "images_sent": 5,
    "missing_images": []
  }
}
```

### Failed Response

When image sending fails, the prediction still succeeds but includes:

```json
{
  // ... normal prediction response fields
  "image_send_result": {
    "success": false,
    "error": "Error message",
    "details": "Additional error details"
  }
}
```

## Error Handling

The image sending feature is designed to be non-blocking:

- If image sending fails, the prediction request still succeeds
- Errors are logged but don't affect the main prediction functionality
- Missing crop images are noted but don't prevent sending available images

## Testing

### Manual Testing Endpoint

Use the test endpoint to manually send images:

```bash
curl -X POST "http://localhost:8000/api/v1/test/send-images?prediction_type=short_term" \
  -H "Content-Type: application/json" \
  -d '["Corn", "Soybean", "Wheat", "Rice", "Cotton"]'
```

### Example Test Commands

```bash
# Test short-term prediction with 5 crops
curl -X POST "http://localhost:8000/api/v1/test/send-images?prediction_type=short_term&crop_names=Corn&crop_names=Soybean&crop_names=Wheat&crop_names=Rice&crop_names=Cotton"

# Test long-term prediction with 12 crops
curl -X POST "http://localhost:8000/api/v1/test/send-images?prediction_type=long_term&crop_names=Corn&crop_names=Soybean&crop_names=Wheat&crop_names=Rice&crop_names=Cotton&crop_names=Potato&crop_names=Tomato&crop_names=Lettuce&crop_names=Carrot&crop_names=Onion&crop_names=Barley&crop_names=Oats"
```

## Implementation Details

### File Structure

```text
Backend/
├── src/services/image_service.py    # Main image service implementation
├── images/                          # Crop image files
├── .env                            # Configuration file
└── main.py                         # Updated with image sending integration
```

### Key Functions

- `send_images_to_api()` - Main function to send images to external API
- `get_crop_image_mapping()` - Maps crop names to image files
- `encode_image_to_base64()` - Converts images to base64 format
- `process_prediction_and_send_images()` - Integrates with prediction pipeline

### Dependencies

Added to `requirements.txt`:

- `aiohttp==3.9.1` - For HTTP client functionality

## Troubleshooting

### Common Issues

1. **Images not sending**
   - Check that `IMAGE_SEND_ENABLED=true` in your `.env` file
   - Verify the `IMAGE_SEND_API_URL` is correct
   - Check logs for error messages

2. **Missing crop images**
   - Ensure image files exist in `Backend/images/`
   - Check that crop names match available image files (case-insensitive)
   - Missing images are logged but don't prevent sending available ones

3. **API authentication issues**
   - Set `IMAGE_SEND_API_KEY` if the external API requires authentication
   - Check API documentation for correct authentication format

4. **Timeout issues**
   - Increase `IMAGE_SEND_TIMEOUT` for slower connections
   - Default timeout is 30 seconds

### Logging

The system logs important events:

- Image sending attempts and results
- Missing crop images
- API errors and timeouts
- Configuration issues

Check the application logs for detailed error information.

## Integration Examples

### Frontend Integration

When calling prediction endpoints, check for the `image_send_result` field in responses:

```javascript
const response = await fetch('/api/v1/predict/month', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    parcel_id: 'P1',
    month: 9,
    top_n: 5,
    ranking_method: 'profit'
  })
});

const data = await response.json();

if (data.image_send_result?.success) {
  console.log(`Successfully sent ${data.image_send_result.images_sent} images`);
} else {
  console.warn('Image sending failed:', data.image_send_result?.error);
}
```

### Backend Integration

To add image sending to custom endpoints:

```python
from src.services.image_service import process_prediction_and_send_images

# After generating predictions
image_result = await process_prediction_and_send_images(
    prediction_result=your_prediction_result,
    prediction_type="short_term",  # or "long_term"
    additional_metadata={"custom_field": "value"}
)
```
