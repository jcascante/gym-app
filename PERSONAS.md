# Gym App - User Personas, Roles & Responsibilities

## Overview

This document defines the user personas for the Gym App platform. The application supports multiple user types ranging from platform administrators to end-user clients, enabling both gym-based and independent coaching scenarios.

---

## Subscription-Based Architecture

### Multi-Tenant Design Philosophy

The Gym App uses a **single-deployment, subscription-based multi-tenancy model** rather than separate deployments per customer. The **subscription is the top-level tenant entity** - whether it's an individual coach or a gym with 50 staff members, everything is organized under a subscription. This architectural approach provides several key benefits:

- **Scalability**: Single codebase and infrastructure serves all customers
- **Cost Efficiency**: Shared resources reduce operational overhead
- **Rapid Updates**: Features and fixes roll out to all customers simultaneously
- **Centralized Management**: Application support team can manage all subscriptions from one platform
- **Simplified Model**: One clear tenant boundary (subscription) instead of multiple overlapping concepts

### Subscription Tiers & Persona Access

Personas and available features are **dynamically determined by subscription type**. Each subscription tier unlocks specific personas and capabilities:

#### Subscription Tier Structure

1. **Individual Coach Subscription**
   - **Available Roles**: Subscription Admin (the coach), Client
   - **Use Case**: Freelance trainers managing their own client roster
   - **Target Market**: Solo fitness entrepreneurs, independent personal trainers
   - **Example**: "Maria's Coaching" with 1 admin (Maria) + 15 clients

   **Resource Limits:**
   - Max Admins: 1
   - Max Coaches: 0 (admin is the coach)
   - Max Clients: 50
   - Storage: 5 GB
   - Monthly Workout Programs: Unlimited
   - Video Uploads: 10 per month

   **Features Enabled:**
   - ✓ Client management
   - ✓ Program creation and assignment
   - ✓ Progress tracking and analytics
   - ✓ Workout logging
   - ✓ In-app messaging
   - ✓ Basic mobile app
   - ✓ Email notifications
   - ✗ Multi-coach collaboration
   - ✗ Advanced analytics
   - ✗ API access
   - ✗ White-label branding
   - ✗ Multi-location support
   - ✗ Custom integrations

2. **Gym Subscription**
   - **Available Roles**: Subscription Admin (multiple allowed), Coach, Client
   - **Use Case**: Single-location gym facilities with staff and member management
   - **Target Market**: Small to medium-sized gyms, fitness studios, boutique studios
   - **Example**: "PowerFit Gym" with 2 admins (owners) + 12 coaches + 300 members

   **Resource Limits:**
   - Max Admins: 5
   - Max Coaches: 25
   - Max Clients: 500
   - Storage: 50 GB
   - Monthly Workout Programs: Unlimited
   - Video Uploads: 100 per month

   **Features Enabled:**
   - ✓ Everything in Individual, plus:
   - ✓ Multi-admin management
   - ✓ Coach accounts and assignment
   - ✓ Member billing integration
   - ✓ Class scheduling
   - ✓ Equipment inventory management
   - ✓ Advanced analytics dashboard
   - ✓ Coach performance reports
   - ✓ Member retention insights
   - ✓ Custom branding (logo, colors)
   - ✓ Bulk operations (mass email, program assignment)
   - ✗ Multi-location support
   - ✗ API access
   - ✗ White-label (full rebrand)
   - ✗ Custom integrations
   - ✗ SSO/SAML authentication

3. **Enterprise Subscription**
   - **Available Roles**: Subscription Admin (multiple), Coach, Client, Location Manager (optional)
   - **Use Case**: Multi-location gyms, franchises, large-scale fitness operations
   - **Target Market**: Gym chains, franchises, corporate wellness programs, large fitness brands
   - **Example**: "FitChain Franchise" with 5 admins + 50 coaches across 10 locations + 5000 members

   **Resource Limits:**
   - Max Admins: Unlimited
   - Max Coaches: Unlimited
   - Max Clients: Unlimited
   - Max Locations: Unlimited
   - Storage: 500 GB (expandable)
   - Monthly Workout Programs: Unlimited
   - Video Uploads: Unlimited
   - API Rate Limit: 10,000 requests/hour

   **Features Enabled:**
   - ✓ Everything in Gym, plus:
   - ✓ **Multi-location management** (locations table, location-based filtering)
   - ✓ **REST API access** (full CRUD operations, webhooks)
   - ✓ **White-label branding** (custom domain, full UI customization)
   - ✓ **Custom integrations** (Zapier, custom webhooks, third-party APIs)
   - ✓ **Advanced reporting** (cross-location analytics, franchise comparisons)
   - ✓ **Data export/import** (bulk CSV, automated backups)
   - ✓ **Priority support** (dedicated account manager, 24/7 support)
   - ✓ **Custom SLAs** (99.9% uptime guarantee)
   - ✓ **Audit trail export** (compliance reports, GDPR data requests)
   - ✓ **Mobile SDK** (build custom mobile apps on top of platform)

---

#### Subscription Tier Comparison Table

| Feature | Individual | Gym | Enterprise |
|---------|-----------|-----|------------|
| **Target Market** | Solo coaches | Single-location gyms | Multi-location franchises |
| **Pricing (Example)** | $49/month | $199/month | Custom pricing |
| **Max Admins** | 1 | 5 | Unlimited |
| **Max Coaches** | 0 (admin coaches) | 25 | Unlimited |
| **Max Clients** | 50 | 500 | Unlimited |
| **Max Locations** | N/A | 1 (implied) | Unlimited |
| **Storage** | 5 GB | 50 GB | 500 GB+ |
| **API Rate Limit** | N/A | N/A | 10,000/hour |
| **Mobile App** | ✓ Basic | ✓ Basic | ✓ Full-featured |
| **Client Management** | ✓ | ✓ | ✓ |
| **Program Creation** | ✓ | ✓ | ✓ |
| **Progress Tracking** | ✓ | ✓ | ✓ |
| **In-app Messaging** | ✓ | ✓ | ✓ |
| **Multi-coach Support** | ✗ | ✓ | ✓ |
| **Class Scheduling** | ✗ | ✓ | ✓ |
| **Billing Integration** | ✗ | ✓ | ✓ |
| **Equipment Inventory** | ✗ | ✓ | ✓ |
| **Advanced Analytics** | ✗ | ✓ | ✓ Enhanced |
| **Custom Branding** | ✗ | ✓ Logo/colors | ✓ Full white-label |
| **Multi-location** | ✗ | ✗ | ✓ |
| **REST API Access** | ✗ | ✗ | ✓ |
| **Custom Integrations** | ✗ | ✗ | ✓ |
| **Priority Support** | Email only | Email + chat | 24/7 dedicated |
| **SLA** | Best effort | 99% uptime | 99.9% uptime |

#### When to Choose Each Tier

**Choose INDIVIDUAL if:**
- You're a solo personal trainer or coach
- You have fewer than 50 clients
- You don't need to collaborate with other coaches
- You want a simple, affordable solution
- You manage everything yourself

**Choose GYM if:**
- You own or manage a single gym or studio
- You have multiple coaches on staff (up to 25)
- You need member billing and class scheduling
- You want analytics on coach and member performance
- You need custom branding (logo, colors)
- You have up to 500 members

**Choose ENTERPRISE if:**
- You operate multiple gym locations
- You're a franchise or gym chain
- You need location-based reporting and analytics
- You want API access for custom integrations
- You want white-label branding (custom domain, full UI)
- You require 99.9% SLA and dedicated support
- You have more than 500 members or 25 coaches
- You need data export/import and audit trail capabilities

---

### Technical Implementation

#### Subscription-to-Persona Mapping

The **subscription is the top-level entity** that determines:
- **Available Roles**: Which personas/roles can be assigned to users within this subscription
- **Feature Flags**: Which application features are enabled
- **Resource Limits**: Maximum coaches, clients, storage, etc.
- **Billing Context**: Payment plans, invoicing, renewal dates

All users belong to a subscription, and all data is scoped to subscriptions.

#### Database Schema

```
subscriptions
├── id (PK)
├── name (e.g., "PowerFit Gym", "Maria's Coaching", "FitChain Franchise")
├── subscription_type (ENUM: INDIVIDUAL, GYM, ENTERPRISE)
├── status (ENUM: ACTIVE, SUSPENDED, CANCELLED)
├── features (JSONB: feature flags enabled for this subscription)
│   Example: {
│     "multi_location": true,
│     "api_access": true,
│     "white_label": true,
│     "sso_enabled": true,
│     "custom_roles": false
│   }
├── limits (JSONB: resource limits for this subscription)
│   Example: {
│     "max_admins": null,  // null = unlimited
│     "max_coaches": null,
│     "max_clients": null,
│     "max_locations": null,
│     "storage_gb": 500,
│     "api_rate_limit": 10000
│   }
├── billing_info (JSONB: payment method, billing cycle, etc.)
├── created_at (timestamp)
├── created_by (FK -> users, nullable for system-created)
├── updated_at (timestamp)
└── updated_by (FK -> users, nullable)

locations (ENTERPRISE only)
├── id (PK)
├── subscription_id (FK -> subscriptions)
├── name (e.g., "Downtown Branch", "West Side Location")
├── address (JSONB: street, city, state, zip, country)
├── contact_info (JSONB: phone, email, manager_name)
├── settings (JSONB: location-specific configuration)
├── is_active (boolean, for soft deletes)
├── created_at (timestamp)
├── created_by (FK -> users)
├── updated_at (timestamp)
└── updated_by (FK -> users)

users
├── id (PK)
├── subscription_id (FK -> subscriptions) ← Single source of truth
├── location_id (FK -> locations, nullable, ENTERPRISE only)
├── role (ENUM: APPLICATION_SUPPORT, SUBSCRIPTION_ADMIN, COACH, CLIENT)
├── email (unique)
├── password_hash
├── profile (JSONB: name, avatar, bio, etc.)
├── is_active (boolean, for soft deletes)
├── last_login_at (timestamp)
├── created_at (timestamp)
├── created_by (FK -> users, nullable for self-registration)
├── updated_at (timestamp)
└── updated_by (FK -> users)

coach_client_assignments (GYM/ENTERPRISE only)
├── id (PK)
├── subscription_id (FK -> subscriptions)
├── location_id (FK -> locations, nullable, ENTERPRISE only)
├── coach_id (FK -> users where role=COACH)
├── client_id (FK -> users where role=CLIENT)
├── assigned_at (timestamp)
├── assigned_by (FK -> users)
├── is_active (boolean)
├── created_at (timestamp)
├── created_by (FK -> users)
├── updated_at (timestamp)
└── updated_by (FK -> users)

audit_log
├── id (PK)
├── subscription_id (FK -> subscriptions, nullable for platform-level events)
├── location_id (FK -> locations, nullable)
├── user_id (FK -> users, nullable for system events)
├── action (ENUM: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, ACCESS, etc.)
├── entity_type (e.g., 'user', 'subscription', 'workout', 'program', 'location')
├── entity_id (UUID of the affected record)
├── changes (JSONB: before/after state for UPDATE, full record for CREATE/DELETE)
├── ip_address (string)
├── user_agent (string)
├── timestamp (timestamp with timezone)
└── metadata (JSONB: additional context)
```

**Key Design Principles:**
- **Subscription = Tenant**: All data isolation happens at subscription boundary
- **No Organization Entity**: Subscription name serves this purpose ("PowerFit Gym")
- **Multiple Admins**: A subscription can have multiple users with `SUBSCRIPTION_ADMIN` role
- **Role Constraints**: Individual subscriptions cannot have `COACH` role (only SUBSCRIPTION_ADMIN who coaches directly)
- **Multi-Location Support**: ENTERPRISE subscriptions can have multiple locations; users can be assigned to specific locations
- **Location-Optional**: `location_id` is nullable - users without location assignment can access all locations in the subscription
- **Feature Flags**: Subscription `features` JSONB field controls which capabilities are enabled
- **Resource Limits**: Subscription `limits` JSONB field enforces quotas (coaches, clients, storage, API calls)
- **Audit Trail**: All tables include created_at/by, updated_at/by; all changes logged to audit_log
- **Soft Deletes**: Users and locations marked inactive rather than deleted (preserves audit trail)

#### Authorization Flow

1. **User Authentication**: JWT token includes `user_id`, `subscription_id`, and optionally `location_id`
2. **Subscription Validation**: Check subscription status (ACTIVE/SUSPENDED/CANCELLED)
3. **Subscription Type Check**: Validate subscription tier (INDIVIDUAL/GYM/ENTERPRISE)
4. **Role Verification**: Ensure user's role is permitted by their subscription tier
   - INDIVIDUAL: Only SUBSCRIPTION_ADMIN and CLIENT allowed
   - GYM/ENTERPRISE: All roles allowed (SUBSCRIPTION_ADMIN, COACH, CLIENT)
5. **Feature Flag Check**: Validate requested action against subscription `features` JSONB
   - Example: API endpoint access requires `features.api_access = true`
   - Example: Multi-location filtering requires `features.multi_location = true`
6. **Resource Limit Enforcement**: Prevent operations exceeding subscription `limits` JSONB
   - Example: Creating new coach fails if current coach count >= `limits.max_coaches`
   - Example: API requests throttled at `limits.api_rate_limit` per hour
7. **Location Filtering** (ENTERPRISE only):
   - If user has `location_id`, filter data to that location
   - If user has no `location_id`, allow access to all locations (subscription admins)
   - SUBSCRIPTION_ADMIN can always access all locations
8. **Row-Level Security**: Apply `subscription_id` filter to all database queries (except APPLICATION_SUPPORT)

### Benefits of This Approach

- **Flexible Upgrades**: Users can change subscription tiers without data migration
- **Granular Access Control**: Fine-tuned permissions based on subscription + role
- **Revenue Optimization**: Easy to introduce new tiers or à la carte features
- **Single Source of Truth**: All customer data in one database with proper isolation
- **Simplified Operations**: No need to manage separate deployments per customer

### Data Isolation & Security

Despite using a single deployment:
- **Row-Level Security**: Database queries automatically filter by `subscription_id`
- **API Middleware**: Enforces subscription context on all requests
- **Audit Logging**: Tracks all cross-subscription access attempts (Application Support access)
- **Encryption**: Sensitive data encrypted at rest and in transit
- **Application Support Access**: Special `APPLICATION_SUPPORT` role can access any subscription for troubleshooting

---

## Persona 1: Application Support / Developer

### Description
Platform-level team member responsible for maintaining application infrastructure, providing technical support to customers, and troubleshooting issues across all subscriptions.

### Profile
- **Technical Level**: High
- **Business Context**: Internal team member (developer, DevOps, customer support engineer)
- **Access Scope**: Cross-subscription (can access any subscription for support/debugging)
- **Primary Goal**: Ensure platform stability, security, and excellent customer experience

### Key Responsibilities
- Provide technical support to subscription admins and users
- Debug issues across customer subscriptions
- Monitor system health, performance, and security
- Manage platform-wide configuration and settings
- Deploy application updates and database migrations
- Access system analytics and usage metrics
- Investigate security incidents or data issues
- Assist with complex billing or subscription problems

### User Goals
- Resolve customer issues quickly and effectively
- Maintain 99.9% platform uptime
- Ensure data security and privacy compliance
- Prevent system abuse and fraud
- Improve platform performance and reliability

### Pain Points
- Balancing support workload across multiple customers
- Reproducing customer-reported bugs in specific subscription contexts
- Managing emergency deployments and rollbacks
- Handling complex multi-tenant data queries safely
- Maintaining audit trails for compliance

### Technical Role Mapping
- **Role Name**: `APPLICATION_SUPPORT`
- **Database Permission Level**: Read/write access to all subscriptions (with audit logging)
- **Special Capabilities**:
  - Cross-subscription access
  - User impersonation for debugging
  - Global configuration management
  - Audit log access
  - Database direct access (production read replica)

---

## Persona 2: Subscription Admin

### Description
Administrator who owns and manages a subscription. For individual coach subscriptions, this is the coach themselves. For gym subscriptions, this can be the owner, manager, or any other authorized admin (multiple admins allowed per subscription).

### Profile
- **Technical Level**: Medium
- **Business Context**:
  - Individual: Solo fitness entrepreneur
  - Gym: Small to medium-sized gym business owner/manager
- **Access Scope**: Full access to their subscription and all users within it
- **Primary Goal**:
  - Individual: Build and retain client base
  - Gym: Grow membership and optimize operations

### Key Responsibilities

**Common to All Subscription Types:**
- Manage subscription settings and billing
- Configure branding and custom settings
- View analytics and reports
- Manage users within the subscription (add, remove, change roles)
- Handle subscription payments and renewals
- Set policies and access rules

**Gym Subscription Specific:**
- Hire, assign, and remove coaches
- Oversee member roster and memberships
- Manage facilities and equipment inventory
- Track coach performance and member satisfaction
- Coordinate schedules across multiple coaches

**Individual Subscription Specific:**
- Directly coach all clients (no delegation to other coaches)
- Create and assign workout programs
- Track client progress personally

### User Goals
- Maintain active, paying subscription
- Maximize ROI from the platform
- Provide excellent service to clients/members
- Scale business efficiently

### Pain Points
- Understanding which subscription tier fits their needs
- Managing billing and payment issues
- Coordinating multiple admins (in gym scenarios)
- Balancing admin duties with actual coaching/training

### Technical Role Mapping
- **Role Name**: `SUBSCRIPTION_ADMIN`
- **Database Permission Level**: Full read/write access to all data within their `subscription_id`
- **Hierarchy**: Can manage all users within subscription (create, update, delete)
- **Special Capabilities**:
  - Billing and subscription management
  - Analytics dashboard
  - User role assignment (within subscription tier limits)
  - Subscription settings configuration
- **Multi-Admin Support**: Multiple users can have this role in gym/enterprise subscriptions

---

## Persona 3: Coach

### Description
Professional trainer who works within a Gym or Enterprise subscription. Coaches are added by Subscription Admins and work with members/clients under the subscription. **This role only exists in Gym and Enterprise subscriptions**, not Individual subscriptions.

### Profile
- **Technical Level**: Medium
- **Business Context**: Employee or contractor of a gym/fitness business
- **Access Scope**: Clients assigned to them within the subscription
- **Primary Goal**: Provide quality training and help clients achieve fitness goals

### Key Responsibilities
- Create and assign workout programs to assigned clients
- Conduct training sessions (individual or group)
- Track and monitor client progress
- Provide form corrections, feedback, and motivation
- Schedule training sessions
- Communicate with clients (messaging, check-ins)
- Report to subscription admins as needed
- Participate in gym community and events

### User Goals
- Help clients achieve fitness goals
- Build strong trainer-client relationships
- Maintain high client satisfaction and retention
- Grow personal reputation and advance career

### Pain Points
- Balancing multiple clients with different needs and schedules
- Limited administrative control (can't change subscription settings)
- Coordinating with other coaches and gym schedule
- Dependence on subscription admin for account management
- Can't directly manage billing or subscription

### Technical Role Mapping
- **Role Name**: `COACH`
- **Database Permission Level**: Read/write access to assigned clients within same `subscription_id`
- **Hierarchy**: Managed by `SUBSCRIPTION_ADMIN`, can view/edit assigned `CLIENT` users
- **Special Capabilities**:
  - Program creation and assignment
  - Client progress tracking
  - Messaging with assigned clients
  - Session scheduling
- **Subscription Type Restriction**: Only available in GYM and ENTERPRISE subscriptions

---

## Persona 4: Client

### Description
End user who receives fitness training and follows workout programs. Clients exist in all subscription types - they can be coached by an individual coach (Individual subscription) or be members of a gym (Gym/Enterprise subscription).

### Profile
- **Technical Level**: Low to Medium
- **Business Context**: Consumer/end user
- **Access Scope**: Personal data and assigned programs only
- **Primary Goal**: Achieve personal fitness goals

### Key Responsibilities
- Follow assigned workout programs
- Log completed workouts and exercises
- Track personal progress (weight, measurements, PRs)
- Communicate with assigned coach
- Attend scheduled training sessions
- Provide feedback on programs and coaching

### User Goals
- Achieve specific fitness outcomes (lose weight, build muscle, improve health)
- Stay motivated and accountable
- Learn proper exercise techniques
- Build sustainable fitness habits
- Get value from coaching investment

### Pain Points
- Staying consistent and motivated
- Understanding proper form and technique
- Tracking progress effectively
- Navigating complex programs or gym equipment
- Justifying cost of coaching/membership
- Unclear who their assigned coach is (in multi-coach gyms)

### Technical Role Mapping
- **Role Name**: `CLIENT`
- **Database Permission Level**: Read/write access to own user data only (within their `subscription_id`)
- **Hierarchy**:
  - In Individual subscriptions: Coached by `SUBSCRIPTION_ADMIN`
  - In Gym/Enterprise subscriptions: May be assigned to specific `COACH` users
- **Special Capabilities**:
  - Workout logging and tracking
  - Personal progress tracking
  - Messaging with assigned coach(es)
  - View assigned programs and schedules

---

## Role Hierarchy & Relationships

### Cross-Subscription Access
```
APPLICATION_SUPPORT (Platform Level - Internal Team)
└── Can access any subscription for support/debugging
```

### Within Individual Subscription
```
Subscription: "Maria's Coaching" (type: INDIVIDUAL)
├── SUBSCRIPTION_ADMIN (Maria - the coach)
│   ├── CLIENT (John)
│   ├── CLIENT (Sarah)
│   └── CLIENT (Mike)
```

### Within Gym/Enterprise Subscription
```
Subscription: "PowerFit Gym" (type: GYM)
├── SUBSCRIPTION_ADMIN (Carlos - owner)
├── SUBSCRIPTION_ADMIN (Ana - co-owner) ← Multiple admins allowed
├── COACH (Trainer Tom)
│   ├── CLIENT (Member 1)
│   ├── CLIENT (Member 2)
│   └── CLIENT (Member 3)
├── COACH (Trainer Lisa)
│   ├── CLIENT (Member 4)
│   └── CLIENT (Member 5)
└── CLIENT (Member 6 - no assigned coach yet)
```

**Key Points:**
- `APPLICATION_SUPPORT` exists outside subscriptions (internal team only)
- All other roles exist within a specific subscription
- `SUBSCRIPTION_ADMIN` can have multiple users in Gym/Enterprise subscriptions
- `COACH` role only exists in Gym/Enterprise subscriptions
- `CLIENT` can optionally be assigned to a specific coach

## Permission Matrix

| Capability | Application Support | Subscription Admin | Coach | Client |
|-----------|---------------------|-------------------|--------|---------|
| **Platform-Level** |
| Access any subscription | ✓ | - | - | - |
| Manage platform config | ✓ | - | - | - |
| View audit logs | ✓ | - | - | - |
| **Subscription-Level** |
| Manage subscription settings | ✓ | ✓ | - | - |
| Manage billing | ✓ | ✓ | - | - |
| Add/remove users | ✓ | ✓ | - | - |
| Assign user roles | ✓ | ✓ (within limits) | - | - |
| View subscription analytics | ✓ | ✓ | Partial | - |
| **Coaching & Programs** |
| Create workout programs | ✓ | ✓ | ✓ | - |
| Assign programs to clients | ✓ | ✓ (all clients) | ✓ (assigned clients) | - |
| View client progress | ✓ | ✓ (all clients) | ✓ (assigned clients) | ✓ (own only) |
| Message clients | ✓ | ✓ (all clients) | ✓ (assigned clients) | - |
| **Personal** |
| Log workouts | ✓ | ✓ | ✓ | ✓ |
| Track own progress | ✓ | ✓ | ✓ | ✓ |
| Manage own profile | ✓ | ✓ | ✓ | ✓ |
| Message coach | - | - | - | ✓ |

**Notes:**
- **Subscription Admin in Individual subscriptions**: Acts as both admin and coach
- **Subscription Admin in Gym subscriptions**: Can add coaches, or coach directly
- **Coach role**: Only exists in Gym/Enterprise subscriptions
- **Application Support**: Access is logged and audited for compliance

---

## Implementation Notes

### Database Considerations

1. **Subscription Table**: Top-level tenant entity
   - `subscription_type` determines available roles
   - JSONB fields for flexible features and limits
   - All user data scoped by `subscription_id`
   - Includes audit fields (created_at/by, updated_at/by)

2. **User Table**: Simple, clean structure
   - Single `role` enum field (APPLICATION_SUPPORT, SUBSCRIPTION_ADMIN, COACH, CLIENT)
   - Foreign key to `subscriptions` table
   - No organization_id needed - subscription IS the tenant
   - `is_active` for soft deletes (preserves audit trail)
   - Includes audit fields (created_at/by, updated_at/by)

3. **Audit Log Table**: Compliance and debugging
   - Immutable append-only log of all user actions
   - Captures authentication, authorization, and data changes
   - JSONB fields for flexible before/after state tracking
   - Async writes to avoid performance impact
   - See "Audit & Compliance" section for details

4. **Coach-Client Assignment**: Optional many-to-many relationship
   - `coach_client_assignments` table
   - Only applies to Gym/Enterprise subscriptions
   - Individual subscriptions: admin coaches all clients directly
   - Includes audit fields for tracking assignments

5. **Multi-Tenancy Strategy**: Subscription-based
   - All queries filtered by `subscription_id` (except APPLICATION_SUPPORT)
   - Row-level security enforces tenant isolation
   - APPLICATION_SUPPORT role bypasses filters (with audit logging)
   - All tables MUST include created_at/by, updated_at/by fields

### Authentication & Authorization

**JWT Token Structure:**
```json
{
  "user_id": "uuid",
  "subscription_id": "uuid",
  "location_id": "uuid",  // nullable, ENTERPRISE only
  "role": "SUBSCRIPTION_ADMIN",
  "subscription_type": "GYM",
  "features": {
    "multi_location": false,
    "api_access": false,
    "white_label": false
  },
  "limits": {
    "max_admins": 5,
    "max_coaches": 25,
    "max_clients": 500,
    "storage_gb": 50
  }
}
```

**Authorization Flow:**
1. Verify JWT signature and expiration
2. Check subscription status (ACTIVE/SUSPENDED/CANCELLED)
3. Validate subscription type and role compatibility (e.g., COACH only in GYM/ENTERPRISE)
4. Enforce role-based permissions (RBAC)
5. Apply feature flags from JWT (validate against subscription `features` JSONB)
6. Check resource limits before mutations (validate against subscription `limits` JSONB)
7. Apply location filtering if `location_id` present (ENTERPRISE only)
8. Filter all queries by `subscription_id` (unless APPLICATION_SUPPORT)

**Special Cases:**
- **APPLICATION_SUPPORT**: Can set `subscription_id` in requests, logged for audit
- **Multiple SUBSCRIPTION_ADMINs**: All have equal permissions within subscription
- **Role constraints**: Prevent creating COACH in INDIVIDUAL subscriptions
- **Location access**:
  - Users with `location_id`: Can only access data for their assigned location
  - Users without `location_id`: Can access all locations within subscription
  - SUBSCRIPTION_ADMIN: Always has access to all locations regardless of `location_id`

### Audit & Compliance

**Audit Fields on All Tables:**
All database tables MUST include these fields for compliance and debugging:
- `created_at` (timestamp with timezone, auto-set on INSERT)
- `created_by` (FK to users, nullable for system/self-registration)
- `updated_at` (timestamp with timezone, auto-updated on UPDATE)
- `updated_by` (FK to users, from JWT token)

**Audit Log Table:**
Dedicated `audit_log` table captures all significant user actions and data changes:

**What Gets Logged:**
1. **Authentication Events**
   - Login (successful and failed attempts)
   - Logout
   - Password reset requests and completions
   - Session expirations

2. **User Management**
   - User creation (with role and subscription)
   - User role changes
   - User deactivation/reactivation
   - User profile updates
   - Password changes

3. **Subscription Management**
   - Subscription creation
   - Subscription type changes (upgrades/downgrades)
   - Subscription status changes (ACTIVE → SUSPENDED → CANCELLED)
   - Billing updates
   - Feature flag changes

4. **Data Changes**
   - Workout program creation/updates/deletion
   - Client assignments to coaches
   - Workout logs and progress updates
   - Any DELETE operations (critical for compliance)

5. **Cross-Subscription Access**
   - ALL APPLICATION_SUPPORT access to any subscription
   - What data was viewed or modified
   - Reason for access (via metadata field)

6. **Security Events**
   - Failed login attempts (potential brute force)
   - Permission denied errors
   - Suspicious activity patterns
   - API rate limit violations

**Audit Log Entry Example:**
```json
{
  "id": "uuid",
  "subscription_id": "uuid",
  "user_id": "uuid",
  "action": "UPDATE",
  "entity_type": "user",
  "entity_id": "uuid-of-modified-user",
  "changes": {
    "before": {"role": "CLIENT", "is_active": true},
    "after": {"role": "COACH", "is_active": true}
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2025-01-15T14:32:00Z",
  "metadata": {
    "reason": "Promoted to coach after certification",
    "request_id": "uuid"
  }
}
```

**Audit Best Practices:**
- **Immutable**: Audit logs are append-only, never updated or deleted
- **Retention**: Keep audit logs for minimum 1 year (configurable per compliance requirements)
- **Indexed**: Index on `user_id`, `subscription_id`, `timestamp`, `action`, `entity_type`
- **Performance**: Write to audit log asynchronously (message queue) to avoid blocking requests
- **Privacy**: Sanitize sensitive data (passwords, tokens) before logging
- **Access Control**: Only APPLICATION_SUPPORT can query audit logs
- **Alerting**: Monitor for suspicious patterns (mass deletions, repeated failures, etc.)

**Implementation Approach:**
1. **Database Triggers**: Automatically populate created_at/by, updated_at/by
2. **API Middleware**: Log all authenticated requests
3. **Service Layer**: Emit audit events for business logic changes
4. **Background Worker**: Consume audit events and write to audit_log table
5. **Monitoring**: Set up alerts for critical audit events

### Future Considerations

**Enhanced Features:**
- **Client multiple coach assignment**: Allow clients to work with multiple coaches (e.g., strength coach + nutrition coach)
- **Coach collaboration**: Shared workout programs and templates across coaches within subscription
- **Client self-service upgrades**: Allow clients to upgrade to personal training within gym membership
- **Mobile SDK enhancements**: Native iOS/Android SDKs for building custom white-label apps
- **Marketplace**: Template library for workout programs (community-created, paid/free)
- **Nutrition tracking**: Meal planning and macro tracking integration
- **Wearable integration**: Sync with Apple Watch, Fitbit, Garmin for automatic workout logging

**Billing & Monetization:**
- **Usage-based billing**: Pay per active client, per GB storage used
- **Add-on features**: À la carte features within tiers (e.g., nutrition tracking, advanced analytics)
- **Overage charges**: Exceed limits temporarily for a fee (instead of hard caps)
- **Annual discounts**: 15-20% discount for annual pre-payment
- **Automatic downgrade**: Payment failure flow (ACTIVE → SUSPENDED → CANCELLED with grace periods)
- **Revenue sharing**: Marketplace commission for template sales
- **Referral program**: Subscription credits for referring other gyms/coaches

**Compliance & Security:**
- **SSO/SAML authentication**: Single sign-on with Okta, Azure AD, Google Workspace for ENTERPRISE tier
- **2FA/MFA**: Multi-factor authentication for sensitive roles
- **HIPAA compliance**: For medical/physical therapy use cases
- **GDPR enhancements**: Right to be forgotten automation, data portability export
- **SOC 2 Type II**: Security audit certification for enterprise customers
- **Penetration testing**: Annual third-party security audits

**Operational Enhancements:**
- **A/B testing framework**: Test features per subscription for product optimization
- **Feature flagging service**: Runtime feature toggling without deployments
- **Usage analytics**: Track feature adoption and engagement metrics
- **Performance monitoring**: Real-time alerts for slow queries, API errors
- **Customer success tooling**: In-app onboarding, feature tours, help center
