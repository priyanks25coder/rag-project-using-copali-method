from app.scheduler.scheduler import cleanup_expired_documents, cleanup_orphaned_s3_files

def expired_documents_handler(event, context):
    cleanup_expired_documents()
    return {"status": "ok"}


def orphaned_s3_handler(event, context):
    cleanup_orphaned_s3_files()
    return {"status": "ok"}