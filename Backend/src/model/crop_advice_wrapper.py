import os, json
from typing import Optional, List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel, ValidationError, Field
from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError

# --------- schema ---------
class CropCare(BaseModel):
    watering_frequency: str = Field(..., description="How often to water (e.g., '2–3x/week; keep soil evenly moist')")
    placement: str = Field(..., description="Optimal placement (e.g., 'full sun; 6–8 hrs; 12–18 in spacing')")
    soil_type: str = Field(..., description="Best soil (e.g., 'well-drained loam; pH 6.0–6.8; rich in organic matter')")

# --------- wrapper ---------
class CropAdviceWrapper:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",   # choose any chat-capable model you have access to
        temperature: float = 0.2,
    ):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature

    SYSTEM_PROMPT = (
        "You are an expert horticulture assistant. "
        "Return concise, practical guidance for home/small-plot growers. "
        "If the crop is ambiguous, assume the most common table/culinary variety. "
        "Always answer in strict JSON with keys: watering_frequency, placement, soil_type. "
        "Use short, specific phrases; include quantities (hours of sun, spacing, pH ranges) when common knowledge."
    )

    def _user_prompt(self, crop: str) -> str:
        return (
            f"Crop: {crop}\n"
            "Return ONLY JSON with these exact keys:\n"
            '{\n'
            '  "watering_frequency": "...",\n'
            '  "placement": "...",\n'
            '  "soil_type": "..."\n'
            '}\n'
            "Guidelines:\n"
            "- Watering: frequency + moisture cue (e.g., top 1 in dry).\n"
            "- Placement: sun hours, wind/frost notes, spacing.\n"
            "- Soil: texture, drainage, pH range, amendments if typical."
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.8, min=1, max=6),
        retry=retry_if_exception_type((APIError, RateLimitError, APITimeoutError, ValidationError, json.JSONDecodeError)),
    )
    def get_crop_care(self, crop: str) -> CropCare:
        # Prefer JSON mode if available on your account; if not, the plain prompt still works.
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": self._user_prompt(crop)},
            ],
            # If your SDK supports it, you can uncomment this for strict JSON:
            # response_format={"type": "json_object"},
        )
        content_raw = resp.choices[0].message.content
        if content_raw is None:
            raise ValueError("No content returned from OpenAI API.")
        content = content_raw.strip()

        # Parse & validate
        data = json.loads(content)
        return CropCare(**data)

    def get_multiple_crop_care(self, crops: List[str]) -> Dict[str, CropCare]:
        """
        Get crop care advice for multiple crops.
        
        Args:
            crops: List of crop names
            
        Returns:
            Dictionary mapping crop names to CropCare objects
        """
        results = {}
        for crop in crops:
            try:
                results[crop] = self.get_crop_care(crop)
            except Exception as e:
                # Log error but continue with other crops
                print(f"Failed to get advice for {crop}: {e}")
                # Provide fallback advice
                results[crop] = CropCare(
                    watering_frequency="Consult local agricultural extension",
                    placement="Refer to seed packet instructions",
                    soil_type="Well-drained soil with appropriate pH"
                )
        return results

# --------- quick demo ---------
if __name__ == "__main__":
    wrapper = CropAdviceWrapper()
    for c in ["tomato", "basil", "strawberry"]:
        try:
            care = wrapper.get_crop_care(c)
            print(c, "→", care.model_dump())
        except Exception as e:
            print(f"Failed for {c}: {e}")
