# Performance Evaluator - Laravel Backend

This is the newly migrated Laravel backend for the Performance Evaluator application.

## 🛠 Prerequisites

-   **PHP 8.2 or higher**
-   **Composer**
-   **Node.js 18 or higher**
-   **SQLite** (enabled in PHP)

## 🚀 Getting Started

1.  **Install PHP Dependencies**
    ```bash
    composer install
    ```

2.  **Install Node Dependencies**
    ```bash
    npm install
    ```

3.  **Setup Environment**
    ```bash
    cp .env.example .env
    php artisan key:generate
    ```

4.  **Setup Database**
    ```bash
    # Ensure database/database.sqlite exists
    # If not, create it:
    # touch database/database.sqlite (Linux/Mac)
    # echo "" > database/database.sqlite (Windows)

    php artisan migrate
    ```

5.  **Migrate Legacy Data (Optional)**
    If you want to pull data from the old Python-based SQLite database:
    ```bash
    php artisan app:migrate-data ../performance.db
    ```

6.  **Compile Assets**
    ```bash
    npm run build
    ```

7.  **Run the Server**
    ```bash
    php artisan serve
    ```

Visit `http://localhost:8000` to access the app.

---

## 🏗 Key Components

-   **CollectorService**: Handles GitHub and WakaTime API data retrieval.
-   **ScoreCalculator**: The core logic for calculating developer performance scores.
-   **SyncDeveloperMetrics Job**: A queueable job for background data synchronization.
-   **MetricController**: Provides data for the Dashboard and Team Health charts.
-   **ReportController**: Handles generation and export of PDF/Excel reports.
