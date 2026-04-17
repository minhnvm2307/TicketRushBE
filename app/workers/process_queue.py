import asyncio
import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import RedisKey, get_redis_client
from app.db.session import SessionLocal
from app.repositories.event import EventRepository

logger = logging.getLogger(__name__)


async def process_queues_job():
    """
    Worker xử lý hàng đợi ảo (Virtual Queue).
    Dùng Blocking Pop (bzpopmin) với timeout ngắn để không giam tài nguyên.
    """
    redis_client = get_redis_client()
    settings = get_settings()

    while True:
        # ==========================================
        # BƯỚC 1: Lấy danh sách Event rồi ĐÓNG DB NGAY
        # ==========================================
        db: Session = SessionLocal()
        try:
            event_repo = EventRepository(db)
            active_events = event_repo.list_active_for_queue_processing()
        except Exception as e:
            logger.error(f"Lỗi truy vấn DB: {e}", exc_info=True)
            db.close()
            await asyncio.sleep(5)
            continue
        finally:
            db.close()  # CHỐT: Đóng DB trước khi đi vào block ở Redis

        if not active_events:
            logger.info("Không có sự kiện đang Active. Ngủ 10s...")
            await asyncio.sleep(10)
            continue

        # Convert UUID sang string để làm Redis Key
        queue_keys = [RedisKey.event_queue(str(event.id)) for event in active_events]

        # ==========================================
        # BƯỚC 2: Rình bắt User trong Redis (Nằm vùng 3 giây)
        # ==========================================
        try:
            # SỬA LỖI: timeout=3 thay vì 0. 
            # Sau 3s không có ai, nó sẽ nhả ra để vòng lặp quay lại check DB lấy Event mới.
            result = await asyncio.to_thread(redis_client.bzpopmin, queue_keys, timeout=3)
            
            if not result:
                # Không ai vào hàng đợi trong 3s qua, quay lại đầu loop
                continue

            # ==========================================
            # BƯỚC 3: Cấp Token
            # ==========================================
            queue_name, (user_id, _) = result
            
            # SỬA LỖI: ID bây giờ là UUID, không dùng int() nữa
            event_id_str = queue_name.decode("utf-8").split(":")[-2]
            user_id_str = user_id.decode("utf-8")

            access_key = RedisKey.event_access_token(event_id_str, user_id_str)
            
            # Cấp quyền vào luồng thanh toán
            await asyncio.to_thread(
                redis_client.set,
                access_key,
                1,
                ex=settings.queue_token_ttl_minutes * 60,
            )
            logger.info(f"Đã cấp Token cho User [{user_id_str}] tại Event [{event_id_str}]")

        except Exception as e:
            logger.error(f"Lỗi khi xử lý Redis Queue: {e}", exc_info=True)
            await asyncio.sleep(2)