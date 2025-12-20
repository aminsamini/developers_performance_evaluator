This file tracks all meaningful changes made to the project over time.

| ID | Date | Files Modified | Description | Related ID |
| :-- | :-- | :-- | :-- | :-- |
| dehi_0019 | 2025-12-20T19:40:00 | backend/database | Removed old repo and added new user-supplied repo 'aminsamiini-dev/Developing_octopus_front'. Verification pending. | N/A |
| dehi_0018 | 2025-12-20T19:30:00 | backend/database (data fix) | Identified and removed invalid repository URL from database. Manually inserted correct 'owner/repo' format. Updated Frontend validation to strip URLs automatically. | N/A |
| dehi_0017 | 2025-12-20T18:50:00 | start_project.bat, frontend/src/components/* | Changed backend port to 5000 after 8000/8001 proved forbidden/locked. Updated all frontend API calls. | N/A |
| dehi_0016 | 2025-12-20T18:25:00 | backend/.env | Switched DATABASE_URL from sqlite+aiosqlite to sqlite to resolve MissingGreenlet error with synchronous SQLAlchemy usage. | N/A |
| dehi_0015 | 2025-12-20T18:20:00 | backend/main.py, requirements.txt | Fixed regression in main.py (restored missing transaction commit). Ensured greenlet dependency is present for SQLAlchemy. | N/A |
| dehi_0014 | 2025-12-20T18:00:00 | backend/services/git_service.py, backend/services/collector.py | Refactored GitService to use Direct Commits API instead of Search. Updated Collector to default to 30-day lookback window. | N/A |
| dehi_0013 | 2025-12-20T17:55:00 | backend/models.py, backend/services/git_service.py, backend/main.py, frontend/src/ | Added Multiple Repository Support. Updated GitService to count commits per repo. Added RepositoryManager frontend component. | N/A |
| dehi_0012 | 2025-12-20T16:00:00 | start_project.bat | Finalized backend startup command fix. Verified imports work from root context. | N/A |
| dehi_0011 | 2025-12-20T15:55:00 | start_project.bat | Fixed backend Relative Import Error by updating startup script to run uvicorn from project root as module. | N/A |
| dehi_0010 | 2025-12-20T15:40:00 | frontend/src/ | Integrated PrimeVue (Aura Theme). Refactored Dashboard and AddDeveloperForm to use PrimeVue components. | N/A |
| dehi_0009 | 2025-12-20T14:35:00 | backend/main.py, frontend/src/ | Added CORS to backend. Implemented Dashboard and AddDeveloperForm Vue components. | N/A |
| dehi_0008 | 2025-12-20T13:00:00 | backend/services/, backend/main.py | Implemented Git and WakaTime data collection services and added /sync endpoint. | N/A |
| dehi_0007 | 2025-12-20T12:55:00 | backend/models.py, backend/database.py, backend/main.py | Implemented SQLAlchemy database schema with Developer and Metric models. Auto-create tables on startup. | N/A |
| dehi_0006 | 2025-12-20T12:40:00 | backend/.env | Created .env file template for API tokens and database configuration. | N/A |
| dehi_0005 | 2025-12-20T12:35:00 | frontend/vite.config.ts, start_project.bat | Changed Vite port to 8080 due to persistent EACCES on 3000. | N/A |
| dehi_0004 | 2025-12-20T12:08:00 | frontend/vite.config.ts, start_project.bat | Changed Vite server port to 3000 and enabled host binding to fix permissions error. | N/A |
| dehi_0003 | 2025-12-20T12:10:00 | start_project.bat | Created Windows Batch script for one-click project startup. | N/A |
| dehi_0002 | 2025-12-20T12:05:00 | frontend/ | Switched frontend from Next.js to Vue.js (Vite + TypeScript). Removed old frontend directory. | N/A |
| dehi_0001 | 2025-12-20T09:40:00 | backend/requirements.txt, frontend/ | Initial Project Setup: Created backend directory with requirements.txt, initialized Next.js frontend. | N/A |
