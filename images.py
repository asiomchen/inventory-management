import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Tuple

config = cloudinary.config(secure=True)


def upload_image(image_path) -> Tuple[str, str]:

    upload_result = cloudinary.uploader.upload(
                image_path,
                resource_type="image",
                folder="/flask_test",
            )
    secure_url = upload_result["secure_url"]
    public_id = upload_result["public_id"]
    optimized_url = cloudinary.utils.cloudinary_url(public_id, fetch_format="auto", quality="auto")[0]
    return optimized_url, public_id

def delete_image(public_id):
    cloudinary.uploader.destroy(public_id)

def deliver_image(public_id, width, height):
    return cloudinary.utils.cloudinary_url(public_id, width=width, height=height, crop="fill")[0]

if __name__ == "__main__":
    upload_image("uploads/test_product_1.png")