Week 1 checklist
Week 1 is about foundations: clarity, architecture, and basic scaffolding. Here’s a concise checklist per role.

Founder / Product
 Write 1–2 page StyluS MVP spec (core loop, AI features, target user).
 Define success metrics for MVP (e.g., onboarding completion, items added, OOTD usage).
 Approve initial feature priority: onboarding → wardrobe → OOTD → assistant → calendar.
 Schedule short kickoff with entire team to align on vision and Week 1 goals.
 Identify 5–10 potential early users for later interviews/usability tests.

UI/UX Designer
 Map information architecture (screens: Auth, Onboarding, Wardrobe, Dashboard, Calendar, Assistant, Insights).
 Draw core user flows (new user: signup → onboarding → add items → OOTD; returning user: dashboard → assistant).
 Create lowfi wireframes for: onboarding, wardrobe add flow, dashboard with OOTD.
 Align with Founder on which fields/steps are musthave vs nicetohave in onboarding.
 Share early wires with FE + BE to inform routes and data models.

Frontend Engineer (Next.js)
 Initialize Next.js + TypeScript project.​
 Install Tailwind CSS and shadcn/ui; configure base theme.​
 Set up basic app layout (mobilefirst container, nav/shell).
 Create placeholder routes: /login, /onboarding, /wardrobe, /dashboard, /calendar, /assistant.
 Integrate Supabase client for auth (env vars, basic signin/signup functions).​
 Implement /login and /signup pages (very simple forms, no styling polish yet).

Backend / Supabase Engineer
 Create Supabase project (auth enabled) and share keys with team.​
 Define initial schema draft for:
 user_profiles (style, colors, contexts, goals).
 wardrobe_items (userId, imageUrl, category, colors, tags, etc.).
 outfit_recommendations and outfit_logs.
 Enable and test Row Level Security for userscoped tables.​
 Set up Supabase storage bucket for wardrobe images.​
 Create basic API endpoints or server actions plan for profile and wardrobe (even if not implemented yet).
 Align with AI/ML on data shapes needed for tagging and recommendation.

AI/ML Engineer
 Clarify list of required tags per item (category, dominant color, colors[], season, formality, sleeves).
 Draft rulebased outline for outfit engine (filters: occasion, weather, style; ranking signals: wear frequency, recency, feedback, variety).
 Set up Python project with virtualenv; install FastAPI, requests, Pillow, OpenCV.​
 Create minimal FastAPI app with /health endpoint running locally.​
 Implement helper to load image from URL and return basic info (size, simple dominant color).
 Write short doc of planned AI endpoints (/ai/tag-item, /ai/generate-outfit, /ai/assistant, /ai/classify-event) with tentative request/response JSON.

At the end of Week 1, the team should have: shared MVP spec, core flows, project scaffolding (Next.js + Supabase + FastAPI), and a clear AI/API contract
