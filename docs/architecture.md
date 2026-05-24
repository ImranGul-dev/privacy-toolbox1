# Architecture

Next.js App Router renders marketing and tool pages. FastAPI accepts uploads, creates jobs, exposes job polling and short-lived downloads. Celery workers run image, PDF, Office and verification processing. Redis is the queue/backend. Postgres is included for the future paid/auth layer but not required by the anonymous MVP.

Queue flow: upload -> validate -> temp storage -> job route -> Celery task -> scanner/cleaner -> verification scan -> signed download token -> automatic cleanup.
