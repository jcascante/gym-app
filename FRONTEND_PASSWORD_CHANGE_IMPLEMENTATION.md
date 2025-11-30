# Frontend Password Change Implementation

## Overview

The frontend has been updated to support the forced password change feature for newly created clients. When a coach creates a new client with a temporary password, the client will be required to change their password on first login before accessing any other features.

## Changes Made

### 1. Type Definitions (`frontend/src/types/user.ts`)

**Updated LoginResponse interface:**
```typescript
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  password_must_be_changed: boolean;  // NEW FIELD
}
```

**Added new types:**
```typescript
export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  message: string;
  detail?: string;
}
```

### 2. Auth Service (`frontend/src/services/auth.ts`)

**Added changePassword function:**
```typescript
export async function changePassword(data: ChangePasswordRequest): Promise<ChangePasswordResponse> {
  return apiFetch<ChangePasswordResponse>('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

### 3. Auth Context (`frontend/src/contexts/AuthContext.tsx`)

**Added password state management:**
- Added `passwordMustBeChanged` state variable
- Updated `login` function to capture the flag from login response
- Exposed `passwordMustBeChanged` in context
- Reset flag on logout

**Changes:**
```typescript
const [passwordMustBeChanged, setPasswordMustBeChanged] = useState<boolean>(false);

// In login function:
setPasswordMustBeChanged(response.password_must_be_changed || false);

// In logout function:
setPasswordMustBeChanged(false);

// In context value:
passwordMustBeChanged,
```

### 4. Login Page (`frontend/src/pages/Login.tsx`)

**Updated login flow:**
```typescript
const { login, passwordMustBeChanged } = useAuth();

// After successful login:
if (passwordMustBeChanged) {
  navigate('/change-password', {
    state: { passwordMustBeChanged: true }
  });
} else {
  navigate('/dashboard');
}
```

### 5. New Change Password Page (`frontend/src/pages/ChangePassword.tsx`)

**Features:**
- Accepts current password, new password, and confirmation
- Client-side validation:
  - Minimum 8 characters
  - New password must match confirmation
  - New password must be different from current
- Handles both forced (first login) and voluntary password changes
- Forced mode: Shows warning message, redirects to dashboard after success, logout button on cancel
- Voluntary mode: Standard form, navigates back after success
- Error handling with user-friendly messages
- Success message with auto-redirect
- Loading states during API calls

**Styling** (`frontend/src/pages/ChangePassword.css`):
- Modern gradient background matching login page
- Responsive card-based design
- Clear visual feedback for success/error states
- Warning banner for forced password changes
- Mobile-responsive layout

### 6. Routing (`frontend/src/App.tsx`)

**Added new route:**
```typescript
<Route
  path="/change-password"
  element={
    <ProtectedRoute>
      <ChangePassword />
    </ProtectedRoute>
  }
/>
```

Note: The route is protected, ensuring only authenticated users can access it.

## User Flow

### For New Clients (Forced Password Change)

1. **Coach creates client** → Random password generated
2. **Client receives credentials** → Via email (TODO) or direct communication
3. **Client logs in** → Enters temporary password
4. **Automatic redirect** → Sent to `/change-password` page with forced mode
5. **Change password** → Must enter current (temp) and new password
6. **Success** → Redirected to dashboard with full access
7. **Cancel** → Logs out (cannot access other features)

### For Existing Users (Voluntary Change)

1. **Navigate to settings** → (Future: Add link in user menu)
2. **Access change password** → Navigate to `/change-password`
3. **Change password** → Enter current and new password
4. **Success** → Navigate back to previous page
5. **Cancel** → Navigate back without changes

## Security Features

### Client-Side Validation
- Minimum password length (8 characters)
- Password confirmation matching
- Prevents reusing current password
- Clear error messages for validation failures

### Server-Side Integration
- Uses secure API endpoint `/api/v1/auth/change-password`
- Requires authentication (JWT token)
- Server validates current password before allowing change
- Password change clears `password_must_be_changed` flag

### UX Security
- Masked password inputs
- Clear distinction between forced and voluntary changes
- Cannot bypass forced password change
- Automatic logout if cancel during forced change

## Testing the Feature

### Manual Test Steps

1. **Create a new test client:**
   ```bash
   # Login as coach
   POST /api/v1/auth/login
   {
     "username": "coach@testgym.com",
     "password": "Coach123!"
   }

   # Create client
   POST /api/v1/coaches/me/clients
   {
     "email": "newclient@example.com",
     "first_name": "Test",
     "last_name": "Client",
     "phone_number": "+1-555-0123"
   }
   ```

2. **Note the generated password** (from backend logs or database)

3. **Login as new client:**
   - Navigate to http://localhost:5173/login
   - Enter new client email and temporary password
   - Should automatically redirect to `/change-password`
   - Warning message should be visible

4. **Change password:**
   - Enter temporary password as current
   - Enter new password (min 8 chars)
   - Confirm new password
   - Submit form
   - Should see success message and redirect to dashboard

5. **Verify access:**
   - Should now have full access to all features
   - Can navigate normally
   - No more password change prompts

6. **Test voluntary change:**
   - Navigate directly to `/change-password`
   - Should see normal password change form
   - Change password successfully
   - Should navigate back

## Files Modified/Created

### Modified Files
- `frontend/src/types/user.ts` - Added types for password change
- `frontend/src/services/auth.ts` - Added changePassword function
- `frontend/src/contexts/AuthContext.tsx` - Added password flag state
- `frontend/src/pages/Login.tsx` - Added redirect logic
- `frontend/src/App.tsx` - Added route

### New Files
- `frontend/src/pages/ChangePassword.tsx` - Change password component
- `frontend/src/pages/ChangePassword.css` - Styling

## Future Enhancements

1. **Email Notifications**
   - Send temporary password to client via email
   - Include instructions and login link

2. **Password Strength Indicator**
   - Visual indicator showing password strength
   - Requirements checklist (uppercase, lowercase, numbers, special chars)

3. **Settings Integration**
   - Add "Change Password" link in user menu
   - Add to user profile/settings page

4. **Password History**
   - Prevent reuse of last N passwords
   - Display password last changed date

5. **Enhanced Validation**
   - Enforce stronger password requirements
   - Add complexity rules (uppercase, lowercase, numbers, symbols)

6. **Internationalization**
   - Add translation keys for all text
   - Support multiple languages

7. **Accessibility**
   - Add ARIA labels
   - Improve keyboard navigation
   - Add screen reader support

## Integration with Backend

The frontend integrates with these backend endpoints:

- `POST /api/v1/auth/login` - Returns `password_must_be_changed` flag
- `POST /api/v1/auth/change-password` - Changes password and clears flag
- All protected endpoints - Return 403 if password must be changed

The backend ensures:
- New clients have `password_must_be_changed=True`
- Protected endpoints block access until password is changed
- Password change endpoint clears the flag
- Login returns current flag status

## Status

✅ **Frontend Implementation Complete**

All components are in place and the feature is ready for testing with the backend server running.
