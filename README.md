# Performance Evaluator (Laravel Migration)

**Performance Evaluator** has been migrated to a full-featured Laravel 11 / Inertia.js / Vue 3 application.

## 🚀 Setup Instructions (Laravel Version)

Navigate to the new project directory:
```bash
cd performance-optimizer-laravel
```

### 1. Install Dependencies
You need both PHP and Node.js dependencies:

```bash
# Install PHP dependencies
composer install

# Install Node.js dependencies
npm install
```

### 2. Environment Configuration
Copy the example environment file and generate an application key:

```bash
cp .env.example .env
php artisan key:generate
```

*Note: Ensure `DB_CONNECTION=sqlite` in your `.env`. Laravel will use `database/database.sqlite` by default.*

### 3. Database Migration
Run migrations to set up the schema:

```bash
# Create the sqlite file if it doesn't exist
touch database/database.sqlite

# Run migrations
php artisan migrate
```

#### Optional: Migrate Legacy Data
If you have data in the old `performance.db`, you can migrate it:
```bash
php artisan app:migrate-data ../performance.db
```

### 4. Build Assets
Compile the frontend assets:

```bash
npm run build
```

### 5. Start the Application
You will need two terminals running (or run in background):

**Terminal 1: Laravel Server**
```bash
php artisan serve
```

**Terminal 2: Vite Dev Server (Optional for development)**
```bash
npm run dev
```

The application will be available at `http://127.0.0.1:8000`.

---

## 🛠 Features (New Architecture)
- **Backend**: Laravel 11, Eloquent ORM, SQLite.
- **Frontend**: Vue 3, Inertia.js, Tailwind CSS, PrimeVue.
- **Auth**: Laravel Jetstream (Optional).
- **Background Jobs**: Automated metrics sync via Laravel Queues.
- **Reporting**: PDF and Excel exports powered by PHP libraries.
