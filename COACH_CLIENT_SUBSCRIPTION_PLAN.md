# Coach and Client Subscription Module - Planning Document

## Overview
A subscription-based platform where coaches pay for access and can manage multiple clients. Clients use the platform for free and can work with multiple coaches simultaneously.

## Business Model

### Subscription Model
- **Coaches**: Pay monthly/annual subscription to access the platform
- **Clients**: Free access to the platform
- **Revenue**: Generated from coach subscriptions only

### Key Requirements
1. Coaches must have an active subscription to use the platform
2. Subscription tiers limit the number of active clients a coach can manage
3. Many-to-many relationship: One client can work with multiple coaches, one coach can have multiple clients
4. Start with manual subscription management (no payment integration initially)

## User Roles

### Coach
- Primary paying user of the platform
- Can create and assign workout programs
- Can manage multiple clients
- Has subscription tier that determines client limit
- Can view and track client progress
- Can communicate with clients

### Client
- Free user of the platform
- Can be assigned to multiple coaches
- Receives programs from coaches
- Tracks workouts and progress
- Can communicate with their coaches

### Admin (Future)
- Manages coach subscriptions
- Platform oversight and analytics
- User management

## Subscription Tiers

### Tier 1: Starter Coach
- **Price**: $29/month (manual)
- **Client Limit**: 10 active clients
- **Features**:
  - Basic program creation
  - Client progress tracking
  - Messaging with clients
  - Basic analytics

### Tier 2: Professional Coach
- **Price**: $79/month (manual)
- **Client Limit**: 50 active clients
- **Features**:
  - All Starter features
  - Advanced program templates
  - Detailed analytics and reports
  - Client check-in system
  - Priority support

### Tier 3: Elite Coach
- **Price**: $149/month (manual)
- **Client Limit**: Unlimited clients
- **Features**:
  - All Professional features
  - Team coaching capabilities
  - Custom branding options
  - API access (future)
  - Dedicated support

## Database Schema

### Users Table (Enhanced)
```python
class User(BaseModel):
    id: UUID (PK)
    email: str (unique)
    hashed_password: str
    full_name: str
    role: Enum('coach', 'client', 'admin')
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### Coach Profile Table
```python
class CoachProfile(BaseModel):
    id: UUID (PK)
    user_id: UUID (FK -> users.id)
    subscription_tier: Enum('starter', 'professional', 'elite')
    subscription_status: Enum('active', 'inactive', 'trial', 'cancelled', 'past_due')
    subscription_start_date: datetime
    subscription_end_date: datetime (nullable)
    client_limit: int (computed from tier)
    bio: str (nullable)
    specializations: JSON (nullable)
    certifications: JSON (nullable)
    created_at: datetime
    updated_at: datetime
```

### Client Profile Table
```python
class ClientProfile(BaseModel):
    id: UUID (PK)
    user_id: UUID (FK -> users.id)
    date_of_birth: date (nullable)
    fitness_goals: JSON (nullable)
    health_conditions: JSON (nullable)
    emergency_contact: JSON (nullable)
    created_at: datetime
    updated_at: datetime
```

### Coach-Client Relationship Table (Many-to-Many)
```python
class CoachClientRelationship(BaseModel):
    id: UUID (PK)
    coach_id: UUID (FK -> coach_profiles.id)
    client_id: UUID (FK -> client_profiles.id)
    status: Enum('active', 'inactive', 'pending', 'terminated')
    relationship_start_date: datetime
    relationship_end_date: datetime (nullable)
    notes: str (nullable)  # Coach's notes about this client
    created_at: datetime
    updated_at: datetime

    # Composite unique constraint on (coach_id, client_id)
```

### Subscription History Table (Audit Trail)
```python
class SubscriptionHistory(BaseModel):
    id: UUID (PK)
    coach_profile_id: UUID (FK -> coach_profiles.id)
    tier: Enum('starter', 'professional', 'elite')
    status: Enum('active', 'inactive', 'trial', 'cancelled', 'past_due')
    start_date: datetime
    end_date: datetime (nullable)
    payment_method: str (nullable)
    amount: decimal (nullable)
    notes: str (nullable)
    created_at: datetime
```

## Business Logic & Workflows

### Coach Registration Flow
1. User signs up with email/password
2. Select role as "Coach"
3. Choose subscription tier
4. Admin manually activates subscription (for now)
5. Coach profile created with `subscription_status='trial'` or `'active'`
6. Coach can start onboarding clients

### Client Registration Flow
1. User signs up with email/password
2. Select role as "Client"
3. Client profile created automatically
4. Client can be invited by coaches or search for coaches (future)

### Coach Invites Client Flow
1. Coach enters client email
2. System checks if client exists:
   - If exists: Create coach-client relationship with `status='pending'`
   - If not: Send invitation email, create user when they accept
3. Client accepts invitation
4. Relationship status changes to `status='active'`
5. Coach can now assign programs to client

### Client Limit Enforcement
1. Before accepting a new client, check coach's current active client count
2. Compare against `client_limit` from subscription tier
3. If at limit: Prevent new relationships, show upgrade message
4. If under limit: Allow new relationship

**SQL Query for Active Client Count:**
```sql
SELECT COUNT(*)
FROM coach_client_relationships
WHERE coach_id = ?
AND status = 'active'
```

### Subscription Status Checks
- Middleware/decorator to check coach subscription status on protected routes
- If subscription is inactive/cancelled/past_due:
  - Block program creation
  - Block new client invitations
  - Allow read-only access to existing data
  - Show prominent upgrade/renew message

## API Endpoints

### Authentication & Users
- `POST /api/v1/auth/register` - Register new user (coach or client)
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile

### Coach Management
- `GET /api/v1/coaches/me/profile` - Get coach's own profile with subscription details
- `PUT /api/v1/coaches/me/profile` - Update coach profile
- `GET /api/v1/coaches/me/subscription` - Get subscription details and usage
- `GET /api/v1/coaches/me/clients` - List all coach's clients (with status)
- `POST /api/v1/coaches/me/clients/invite` - Invite new client
- `GET /api/v1/coaches/me/clients/{client_id}` - Get specific client details
- `PUT /api/v1/coaches/me/clients/{client_id}` - Update client relationship (status, notes)
- `DELETE /api/v1/coaches/me/clients/{client_id}` - Terminate client relationship

### Client Management
- `GET /api/v1/clients/me/profile` - Get client's own profile
- `PUT /api/v1/clients/me/profile` - Update client profile
- `GET /api/v1/clients/me/coaches` - List all client's coaches
- `GET /api/v1/clients/me/invitations` - List pending coach invitations
- `POST /api/v1/clients/me/invitations/{invitation_id}/accept` - Accept coach invitation
- `POST /api/v1/clients/me/invitations/{invitation_id}/decline` - Decline coach invitation

### Admin (Future)
- `GET /api/v1/admin/coaches` - List all coaches
- `PUT /api/v1/admin/coaches/{coach_id}/subscription` - Update coach subscription
- `GET /api/v1/admin/stats` - Platform statistics

## Frontend Components & Pages

### Coach Dashboard
- Subscription status banner (if trial/expiring/inactive)
- Client count vs limit indicator
- List of active clients
- Quick actions: Invite client, create program
- Subscription management button

### Client Management Page (Coach View)
- Searchable/filterable list of clients
- Client cards showing: name, status, programs assigned, last activity
- "Invite Client" button (disabled if at limit)
- Client detail view with relationship notes

### Coach List Page (Client View)
- List of all coaches client works with
- Coach cards showing: name, specialization, assigned programs
- Pending invitations section

### Subscription Management Page (Coach View)
- Current tier and features
- Usage statistics (clients, programs created, etc.)
- Upgrade/downgrade options
- Billing history (when payment integration added)

## Authorization Rules

### Coach Permissions
- ✅ Create/edit/delete their own programs
- ✅ View/edit their own clients
- ✅ Assign programs to their own clients
- ✅ View progress of their own clients
- ❌ View/edit other coaches' data
- ❌ Access client data for clients they're not connected to

### Client Permissions
- ✅ View their own profile and data
- ✅ View programs assigned by their coaches
- ✅ Log workouts and track progress
- ✅ View their coaches' public profiles
- ❌ Create or modify programs
- ❌ Access other clients' data

### Subscription-Based Restrictions (Coach)
- If subscription inactive:
  - ❌ Create new programs
  - ❌ Invite new clients
  - ❌ Assign programs to clients
  - ✅ View existing data (read-only)
- If at client limit:
  - ❌ Invite new clients
  - ✅ All other normal operations

## Implementation Phases

### Phase 1: Core User Management (Foundation)
1. Enhance User model with role field
2. Create CoachProfile and ClientProfile models
3. Create CoachClientRelationship model
4. Implement registration with role selection
5. Create basic profile endpoints

### Phase 2: Subscription System
1. Add subscription fields to CoachProfile
2. Create subscription tier configuration
3. Implement subscription status checks (middleware)
4. Create subscription management endpoints
5. Add client limit enforcement logic
6. Create SubscriptionHistory model for audit trail

### Phase 3: Coach-Client Relationships
1. Implement client invitation system
2. Create coach-client relationship endpoints
3. Build client management UI for coaches
4. Build coach list UI for clients
5. Add relationship status management

### Phase 4: Frontend Integration
1. Build coach dashboard with subscription status
2. Build client management interface
3. Implement client onboarding flow
4. Add subscription upgrade prompts
5. Create admin tools for manual subscription management

### Phase 5: Enhanced Features (Future)
1. Payment integration (Stripe)
2. Automated billing and renewals
3. Trial period automation
4. Email notifications
5. Advanced analytics
6. Team/organization features

## Migration Strategy

### For Existing Users
If there are existing users in the database:
1. Add role column with default value
2. Prompt existing users to select role on next login
3. Create corresponding profile (coach or client)
4. Migrate any existing data to appropriate profile

### Database Migration Steps
1. Create new tables: coach_profiles, client_profiles, coach_client_relationships, subscription_history
2. Add role column to users table
3. Create indexes on foreign keys and frequently queried fields
4. Add constraints and triggers for data integrity

## Security Considerations

1. **Role-Based Access Control (RBAC)**
   - Use FastAPI dependencies to check user role
   - Validate user has permission for requested resource
   - Separate endpoints by role where appropriate

2. **Subscription Validation**
   - Check subscription status on every protected coach endpoint
   - Cache subscription status per request to avoid multiple DB queries
   - Graceful degradation to read-only mode

3. **Data Privacy**
   - Coaches can only access their connected clients
   - Clients can only access their connected coaches
   - No cross-coach or cross-client data leakage

4. **Audit Trail**
   - Log all subscription changes
   - Log all coach-client relationship changes
   - Maintain history for compliance

## Open Questions & Future Considerations

1. **Client Discovery**: How do clients find coaches?
   - Coach marketplace/directory?
   - Invitation-only?
   - Both?

2. **Client Limits**: What happens when coach downgrades and exceeds new limit?
   - Grandfather existing clients?
   - Force termination of relationships?
   - Grace period?

3. **Coach Specializations**: Should coaches have specialization tags for filtering?
   - Strength training
   - Nutrition
   - Cardio/endurance
   - Rehabilitation

4. **Multi-Coach Coordination**: How do multiple coaches coordinate for shared clients?
   - Shared notes?
   - Separate programs per coach?
   - Communication between coaches?

5. **Trial Period**: Should new coaches get a free trial?
   - 14-day trial?
   - Limited features?
   - Limited clients?

6. **Refund Policy**: What's the refund policy for subscription cancellations?

## Success Metrics

1. **Coach Adoption**: Number of active coach subscriptions
2. **Client Engagement**: Number of active clients per coach
3. **Subscription Upgrades**: Conversion rate from lower to higher tiers
4. **Churn Rate**: Coach subscription cancellation rate
5. **Usage Metrics**: Programs created, workouts logged, client interactions

---

**Next Steps**: Review this plan, make adjustments, then proceed to Phase 1 implementation.
