# Implementation Roadmap - Phase 2 & Beyond

**Status**: Phase 1 complete (Workout Tracking Core), Ready for Phase 2

---

## Phase 2: Workout Logging UI & Exercise Tracking
**Estimated Time**: 1-2 weeks  
**Priority**: High (MVP blocker)

### 2.1 ExerciseLog Model
Create `backend/app/models/exercise_log.py` to track per-exercise performance:
- Fields: WorkoutLog reference, Exercise reference, sets, reps, weight, RPE (rate of perceived exertion)
- Relationships: Links to WorkoutLog and Exercise
- Migration: Run `uv run alembic revision --autogenerate`

### 2.2 ExerciseLogService
Create `backend/app/services/exercise_log_service.py` with methods for:
- Create exercise log entries
- Get exercise history by exercise/client
- Calculate strength progression (weight increase over time)
- Get personal records (1RM estimates)

### 2.3 Workout Logging UI Component
Create `frontend/src/pages/WorkoutLogger.tsx`:
- Display current day's exercises from assigned program
- Input fields for each exercise (sets/reps/weight)
- RPE/notes field
- Real-time validation
- Submit to POST `/api/v1/workouts` with exercise logs

### 2.4 Connect in ClientDetail
Update ClientDetail.tsx to navigate to WorkoutLogger when "Log Workout" clicked

---

## Phase 3: Analytics & Progress Tracking
**Estimated Time**: 1-2 weeks  
**Priority**: Medium

### 3.1 Progress Page Component
Create `frontend/src/pages/ClientProgress.tsx`:
- Show strength progression charts (weight increases over time)
- Display workout frequency (days completed vs scheduled)
- Show streak calculations and adherence metrics
- Compare current vs previous cycles

### 3.2 ProgressService
Create `backend/app/services/progress_service.py`:
- Calculate strength progression
- Calculate adherence rates
- Generate milestone achievements
- Streak calculations

### 3.3 Dashboard Enhancements
Update ClientDashboard to show:
- Current streak (consecutive completed workouts)
- This week's completion rate
- Next scheduled workout

---

## Phase 4: Profile & Media Management
**Estimated Time**: 1 week  
**Priority**: Medium

### 4.1 Profile Photo Upload Service
Implement `backend/app/services/profile_service.py`:
- Accept multipart file upload
- Store in cloud storage (S3, GCS, or local)
- Generate thumbnails
- Return signed URLs

### 4.2 Update User Schema
Add fields to User model:
- `profile_photo_url`: String for URL
- `profile_photo_id`: Reference to uploaded file
- Migration required

### 4.3 Frontend Upload Component
Create upload UI in EditProfileModal

---

## Phase 5: Additional Program Builders
**Estimated Time**: 2-4 weeks  
**Priority**: Low (nice-to-have for MVP)

### 5.1 Hypertrophy PPL Builder
Implement PPL (Push/Pull/Legs) split program builder

### 5.2 General Fitness Builder
Balanced full-body workout program

### 5.3 Athletic Performance Builder
Sport-specific training program

### 5.4 Fat Loss Circuit Builder
High-intensity interval training focused

### Implementation Pattern
1. Create service: `backend/app/services/{builder_type}_builder.py`
2. Inherit from base builder pattern
3. Register in ProgramCalculations
4. Add UI toggle in ProgramBuilder.tsx

---

## Phase 6: Advanced Analytics & Reporting
**Estimated Time**: 2 weeks  
**Priority**: Low

### 6.1 Coach Dashboard Analytics
- Client adherence reports
- Performance trends across client base
- Program effectiveness metrics

### 6.2 Admin Reporting
- System-wide usage metrics
- Subscription performance
- User growth trends

### 6.3 Export Features
- CSV exports of workout data
- PDF reports
- Progress summaries

---

## Known Issues & Quick Fixes

### Currently Implemented But Could Use Enhancement
1. **Email Service**: Requires SMTP config for production
   - Action: Add .env configuration documentation
   
2. **Workout Logger**: Basic create-only, no per-exercise tracking yet
   - Action: Implement ExerciseLog model (Phase 2.1)

3. **Dashboard Stats**: Show real data but missing some calculations
   - Action: Add streak and adherence calculations (Phase 3.2)

### Configuration Needed
1. **Email Settings**: Add to production `.env`
   ```
   EMAIL_USE_MOCK=false
   EMAIL_SMTP_HOST=...
   EMAIL_SMTP_USER=...
   EMAIL_SMTP_PASSWORD=...
   ```

2. **Frontend URL**: Update in production
   ```
   FRONTEND_URL=https://app.example.com
   ```

---

## Testing Checklist Before Deployment

### Backend Tests
- [ ] `uv run pytest` - All tests pass
- [ ] Manual: Create workout via API
- [ ] Manual: Fetch stats and verify calculations
- [ ] Manual: Test email sending (mock mode)
- [ ] Manual: Verify authorization (clients can't access other users' workouts)

### Frontend Tests
- [ ] CoachDashboard displays real stats
- [ ] ClientDashboard displays real stats
- [ ] AdminDashboard displays real stats
- [ ] ClientDetail navigation works
- [ ] No console errors

### Integration Tests
- [ ] End-to-end: Coach creates client → send email → client logs workout → stats update
- [ ] End-to-end: Admin views dashboard → sees correct counts
- [ ] Error handling: Network failures handled gracefully

---

## Deployment Steps

### Pre-Deployment
1. Run full test suite: `uv run pytest`
2. Build frontend: `npm run build`
3. Review database migrations: `uv run alembic current`
4. Check environment variables configured

### Deployment
1. Push to main branch
2. Run migrations on production DB: `alembic upgrade head`
3. Restart backend service
4. Deploy frontend build
5. Verify health check: `GET /api/v1`

### Post-Deployment
1. Monitor error logs
2. Test critical user flows
3. Verify email sending (if enabled)
4. Check dashboard data accuracy

---

## File Reference Quick Links

### New Files Created (Phase 1)
- [WorkoutLog Model](../backend/app/models/workout_log.py)
- [Workout Service](../backend/app/services/workout_service.py)
- [Workout Schemas](../backend/app/schemas/workout.py)
- [Workout API](../backend/app/api/workouts.py)
- [Email Service](../backend/app/services/email_service.py)
- [Admin Service (Frontend)](../frontend/src/services/admin.ts)
- [Workout Service (Frontend)](../frontend/src/services/workouts.ts)

### Modified Files (Phase 1)
- [Main App Setup](../backend/app/main.py)
- [Dependencies](../backend/app/core/deps.py)
- [Config](../backend/app/core/config.py)
- [Coaches API](../backend/app/api/coaches.py)
- [Clients API](../backend/app/api/clients.py)
- [ClientDashboard Component](../frontend/src/pages/ClientDashboard.tsx)
- [AdminDashboard Component](../frontend/src/pages/AdminDashboard.tsx)
- [ClientDetail Component](../frontend/src/pages/ClientDetail.tsx)

---

## Quick Start Commands

### Backend Development
```bash
cd backend

# Setup environment
uv sync --dev

# Create migration (after model changes)
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Run tests
uv run pytest

# Start dev server
uv run uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

### Database
```bash
# View current migrations
uv run alembic current

# See migration history
uv run alembic history

# Rollback last migration
uv run alembic downgrade -1

# Reset database (dev only!)
rm gym_app.db && uv run alembic upgrade head
```

---

## Troubleshooting

### Backend Issues
**Workout stats showing 0 even after logging**
- Check WorkoutLog records exist in DB: `SELECT * FROM workout_logs;`
- Verify status is 'completed' not 'scheduled'
- Check subscription_id matches user's subscription

**Email not sending**
- Ensure EMAIL_USE_MOCK=false and SMTP credentials configured
- Check logs for SMTP error details
- Test with `EMAIL_USE_MOCK=true` (development mode)

**API 403 Forbidden**
- Check user has correct role for endpoint
- Verify subscription is ACTIVE (not suspended/cancelled)
- Check password_must_be_changed flag

### Frontend Issues
**Dashboards showing "--"**
- Open DevTools Console, check for API errors
- Verify backend is running and accessible
- Check network tab for failed requests
- Confirm user is authenticated (has valid token)

**Navigation not working**
- Check router configuration in App.tsx
- Verify page component exists at route path
- Check browser console for navigation errors

---

**Last Updated**: February 18, 2026  
**Next Phase Start**: When Phase 2 requirements are clear
