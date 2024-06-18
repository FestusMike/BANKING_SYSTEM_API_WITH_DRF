from rest_framework import serializers
from .models import CustomerMessage, Picture
from filetype import guess

class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = ["id", "image", "caption"]


class CustomerMessageSerializer(serializers.ModelSerializer):
    pictures = PictureSerializer(many=True, read_only=True)
    image_files = serializers.ListField(
        child=serializers.ImageField(write_only=True), write_only=True, required=False
    )

    class Meta:
        model = CustomerMessage
        fields = [
            "reference_id",
            "message",
            "date_created",
            "date_updated",
            "pictures",
            "image_files",
        ]

    def validate_message(self, value):
        if not value:
            raise serializers.ValidationError("Message is required")
        return value

    def validate_image_files(self, value):
        if not value:
            return value
        for image in value:
            file_type = guess(image.read())
            image.seek(0)
            if file_type is None or file_type.mime not in ["image/jpeg", "image/png"]:
                raise serializers.ValidationError(
                    "Invalid file type. Only JPEG and PNG files are allowed"
                )
            if image.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "Pictures must not be larger than 5MB"
                )
        return value
