from upload import upload_to_x
import os

upload_to_x(
    'generated/catalonia.mp4',
    'Catalonia, p cool huh',
    os.environ.get("X_API_KEY"),
    os.environ.get("X_API_SECRET"),
    os.environ.get("X_ACCESS_TOKEN"),
    os.environ.get("X_ACCESS_TOKEN_SECRET"),
)