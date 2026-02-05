import os
import logging
from livekit import api

logger = logging.getLogger(__name__)


class EgressRecordingManager:
    """
    LiveKit Composite Recording Manager
    Produces ONE playable MP4 for entire room
    """

    def __init__(self):
        self.client = api.EgressClient(
            os.getenv("LIVEKIT_URL"),
            os.getenv("LIVEKIT_API_KEY"),
            os.getenv("LIVEKIT_API_SECRET"),
        )
        self.egress_id = None

        os.makedirs("recordings", exist_ok=True)

    async def start_recording(self, room_name: str, candidate_id: str):
        filepath = f"recordings/{candidate_id}_{room_name}.mp4"

        info = await self.client.start_room_composite_egress(
            api.RoomCompositeEgressRequest(
                room_name=room_name,
                layout="grid",
                file_outputs=[
                    api.EncodedFileOutput(filepath=filepath)
                ],
            )
        )

        self.egress_id = info.egress_id
        logger.info(f"Recording started → {filepath}")

    async def stop_recording(self):
        if not self.egress_id:
            return

        await self.client.stop_egress(self.egress_id)
        logger.info("Recording finalized")
