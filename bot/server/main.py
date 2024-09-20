from quart import Blueprint, Response, request, render_template, redirect
from .error import abort
from bot import TelegramBot 
from bot.config import Telegram, Server , mongo
from math import ceil, floor
from bot.modules.telegram import get_message, get_file_properties
from pymongo import MongoClient

bp = Blueprint('main', __name__)

client = MongoClient(mongo.uri)

db = client[mongo.db]



@bp.route("/api")
async def apiroute():
    #get req arguments
    fp = request.args.get("fp")
    name = request.args.get("name")
    #check if the file exists
    file = db["files"].find_one({"fp":fp})
    if file:
        url = f"{Server.BASE_URL}/{file['ci']}/{file['tg']}"
        return {"status":"success","url":url}
    else:
        checkinqu = db["queue"].find_one({"fp":fp})
        if checkinqu:
            return {"status":"processing","msg":"File in Queue"}
        else:
            db["queue"].insert_one({"fp":fp})
            return {"status":"processing","msg":"Added to queue"}


@bp.route('/')
async def home():
    return f'https://t.me/{Telegram.BOT_USERNAME}'

@bp.route('/<int:channel_id>/<int:file_id>')
async def transmit_file(channel_id,file_id):
    cid = 0-channel_id
    file = await get_message(message_id=int(file_id),channel_id=cid) or abort(404)
    range_header = request.headers.get('Range', 0)

    file_name, file_size, mime_type = get_file_properties(file)
    
    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = 0
        until_bytes = file_size - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        abort(416, 'Invalid range.')

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = ceil(until_bytes / chunk_size) - floor(offset / chunk_size)
    
    headers = {
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        }

    async def file_generator():
        current_part = 1
        async for chunk in TelegramBot.iter_download(file, offset=offset, chunk_size=chunk_size, stride=chunk_size, file_size=file_size):
            if not chunk:
                break
            elif part_count == 1:
                yield chunk[first_part_cut:last_part_cut]
            elif current_part == 1:
                yield chunk[first_part_cut:]
            elif current_part == part_count:
                yield chunk[:last_part_cut]
            else:
                yield chunk

            current_part += 1

            if current_part > part_count:
                break

    return Response(file_generator(), headers=headers, status=206 if range_header else 200)