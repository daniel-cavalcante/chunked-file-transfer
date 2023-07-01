import os
from typing import Any
from flask import (
    Flask,
    Response,
    render_template,
    request,
    stream_with_context,
)
from flask_cors import CORS
from minio import Minio

from werkzeug.utils import secure_filename

TEMPORARY_FILE_DIR = "/tmp/minio-chunked"
TEMPORARY_FILE_NAME = "temporary_file"

PART_SIZE = 10 * 1024 * 1024

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT") or "localhost:9000"
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY") or "minioadmin"
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY") or "minioadmin"
MINIO_IS_SECURE = os.getenv("MINIO_IS_SECURE") or "False"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
storage = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    # accepts capitalization variants as in FALSE, False and false
    secure=MINIO_IS_SECURE.lower() in ["true"],
)


@app.route("/")
def index():
    return render_template("index.html")


def upload_to_storage(bucket_name: str, object_name: str, data: Any) -> bool:
    try:
        if not storage.bucket_exists(bucket_name):
            storage.make_bucket(bucket_name)
        result = storage.put_object(
            bucket_name, object_name, data.stream, length=-1, part_size=10 * 1024 * 1024
        )
    except Exception:
        raise
    else:
        return True if result else False


@app.route("/upload", methods=["POST"])
def upload():
    # todo: set some form of validation after uploading all files
    chunk = request.files["chunk"]
    original_file_id = request.form["originalFileId"]

    name = secure_filename(chunk.filename)
    if name == "":
        # todo: return meaningful message to the client
        return {"success": False}, 500

    success = upload_to_storage(original_file_id, name, data=chunk)
    return {"success": success}, 201


@app.route("/download")
def download():
    bucket_list = [bucket.name for bucket in storage.list_buckets()]
    return bucket_list


def get_part_number(name: str) -> int:
    """Get the part number from the chunk's file name string.

    Example:
        >>> name="file_name.ext.part1of8"
        >>> x=name.split('.part')
        >>> x
        ['file_name.ext', '1of8']
        >>> y=x[-1].split('of')
        >>> y
        ['1', '8']
        >>> int(y[0], base=10)
        1
    """
    x = name.split(".part")
    y = x[-1].split("of")
    return int(y[0], base=10)


def get_name_list(bucket_name) -> list[str]:
    name_list = []
    for item in storage.list_objects(bucket_name, recursive=True):
        name_list.append(item.object_name)

    name_list.sort(key=get_part_number)

    return name_list


def get_download_name(bucket_name):
    name_list = get_name_list(bucket_name)
    # similar to function get_part_number but it takes the file name
    return name_list[0].split(".part")[0]


def get_file_chunks(bucket_name):
    name_list = get_name_list(bucket_name)
    for name in name_list:
        part = storage.get_object(bucket_name, name)
        if part is None:
            break
        yield part.read(PART_SIZE)


@app.route("/download/<string:bucket_name>")
def download_bucket(bucket_name):
    return Response(
        stream_with_context(get_file_chunks(bucket_name)),
        headers={
            "Content-Disposition": f"attachment; filename={get_download_name(bucket_name)}"
        },
    )


if __name__ == "__main__":
    app.run(debug=True)
