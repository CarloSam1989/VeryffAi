import json
import os
from dotenv import load_dotenv

load_dotenv()

MNEMONIC = os.getenv("IOTA_MNEMONIC")
IOTA_NODE_URL = os.getenv("IOTA_NODE_URL", "https://api.shimmer.network")


class IOTAServiceError(Exception):
    pass


def get_iota_client():
    """
    Importa el SDK solo cuando realmente se usa.
    Así Django puede arrancar aunque el paquete falle.
    """
    try:
        from iota_sdk import Client
    except ImportError as e:
        raise IOTAServiceError(
            "No se pudo importar iota_sdk. "
            "Verifica la instalación del paquete o la versión de Python."
        ) from e

    try:
        client = Client(
            nodes=[IOTA_NODE_URL],
            ignore_node_health=True,
        )
        return client
    except Exception as e:
        raise IOTAServiceError(f"Error al crear cliente IOTA: {e}")


def build_hex_data(data: dict) -> str:
    json_string = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return "0x" + json_string.encode("utf-8").hex()


def build_hex_tag(tag_text: str) -> str:
    return "0x" + tag_text.encode("utf-8").hex()


def extract_block_id(block_response):
    if isinstance(block_response, list) and block_response:
        return str(block_response[0])

    if isinstance(block_response, dict):
        return (
            block_response.get("blockId")
            or block_response.get("id")
            or block_response.get("payload", {}).get("blockId")
            or str(block_response)
        )

    return str(block_response)


def publish_payload(payload: dict, tag_text: str = "TangleTonesRegistro") -> dict:
    if not MNEMONIC:
        return {
            "ok": False,
            "block_id": None,
            "status": "failed",
            "error": "IOTA_MNEMONIC no está definido en el .env",
            "payload": payload,
        }

    try:
        client = get_iota_client()
        tag = build_hex_tag(tag_text)
        data = build_hex_data(payload)

        block = client.build_and_post_block(
            secret_manager={"mnemonic": MNEMONIC},
            tag=tag,
            data=data,
        )

        block_id = extract_block_id(block)

        return {
            "ok": True,
            "block_id": block_id,
            "status": "confirmed",
            "error": None,
            "payload": payload,
        }

    except Exception as e:
        return {
            "ok": False,
            "block_id": None,
            "status": "failed",
            "error": str(e),
            "payload": payload,
        }


def register_song_on_iota(song) -> dict:
    payload = {
        "type": "song",
        "title": song.title,
        "artist": song.artist.username,
        "fingerprint": song.fingerprint,
        "song_id": song.id,
        "upload_date": song.upload_date.isoformat() if song.upload_date else None,
        "genres": list(song.genre.values_list("name", flat=True)),
    }
    return publish_payload(payload, tag_text="TangleTonesSong")


def register_album_on_iota(album, album_fingerprint: str) -> dict:
    payload = {
        "type": "album",
        "title": album.title,
        "artist": album.artist.username,
        "album_id": album.id,
        "fingerprint": album_fingerprint,
        "release_date": album.release_date.isoformat() if album.release_date else None,
        "genres": list(album.genre.values_list("name", flat=True)),
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "fingerprint": song.fingerprint,
            }
            for song in album.songs.all()
        ],
    }
    return publish_payload(payload, tag_text="TangleTonesAlbum")