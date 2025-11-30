#!/usr/bin/env python3
"""
Seed Exercise Library

Populates the exercises_library table with default global exercises.
These exercises are available to all subscriptions.
"""
import asyncio
import uuid
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.exercise import Exercise


# Compound Lifts
COMPOUND_LIFTS = [
    {
        "name": "Back Squat",
        "description": "Barbell back squat with bar on upper traps. Keep chest up, knees tracking over toes.",
        "category": "compound",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings", "core"],
        "equipment": ["barbell", "squat_rack", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 180,
    },
    {
        "name": "Front Squat",
        "description": "Barbell front squat with bar on front deltoids. Requires good mobility and core strength.",
        "category": "compound",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["barbell", "squat_rack", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "advanced",
        "default_rest_seconds": 180,
    },
    {
        "name": "Bench Press",
        "description": "Barbell bench press on flat bench. Retract shoulder blades, drive through feet.",
        "category": "compound",
        "muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment": ["barbell", "bench", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 180,
    },
    {
        "name": "Incline Bench Press",
        "description": "Barbell bench press on incline bench (30-45 degrees). Targets upper chest.",
        "category": "compound",
        "muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment": ["barbell", "incline_bench", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 180,
    },
    {
        "name": "Deadlift",
        "description": "Conventional deadlift from floor. Keep back neutral, drive through heels.",
        "category": "compound",
        "muscle_groups": ["hamstrings", "glutes", "back", "core"],
        "equipment": ["barbell", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 240,
    },
    {
        "name": "Romanian Deadlift",
        "description": "RDL emphasizing hamstring stretch. Maintain slight knee bend, hinge at hips.",
        "category": "compound",
        "muscle_groups": ["hamstrings", "glutes", "lower_back"],
        "equipment": ["barbell", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
    {
        "name": "Overhead Press",
        "description": "Standing barbell overhead press. Press bar in straight line, squeeze glutes.",
        "category": "compound",
        "muscle_groups": ["shoulders", "triceps", "core"],
        "equipment": ["barbell", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 180,
    },
    {
        "name": "Barbell Row",
        "description": "Bent-over barbell row. Maintain hip hinge, pull to lower chest.",
        "category": "compound",
        "muscle_groups": ["back", "biceps", "rear_delts"],
        "equipment": ["barbell", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
    {
        "name": "Pull-up",
        "description": "Bodyweight pull-up with pronated (overhand) grip. Full range of motion.",
        "category": "compound",
        "muscle_groups": ["back", "biceps"],
        "equipment": ["pull_up_bar"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
    {
        "name": "Dip",
        "description": "Bodyweight dip on parallel bars. Lean forward for chest emphasis.",
        "category": "compound",
        "muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment": ["dip_bars"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
]

# Upper Body Accessories
UPPER_ACCESSORIES = [
    {
        "name": "Dumbbell Bench Press",
        "description": "DB bench press on flat bench. Greater range of motion than barbell.",
        "category": "isolation",
        "muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment": ["dumbbells", "bench"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 90,
    },
    {
        "name": "Dumbbell Row",
        "description": "Single-arm dumbbell row. Support on bench, pull to hip.",
        "category": "isolation",
        "muscle_groups": ["back", "biceps"],
        "equipment": ["dumbbell", "bench"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 90,
        "is_bilateral": False,
    },
    {
        "name": "Dumbbell Shoulder Press",
        "description": "Seated or standing DB overhead press. Press dumbbells overhead.",
        "category": "isolation",
        "muscle_groups": ["shoulders", "triceps"],
        "equipment": ["dumbbells", "bench"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 90,
    },
    {
        "name": "Lateral Raise",
        "description": "Standing dumbbell lateral raise. Raise arms to shoulder height.",
        "category": "isolation",
        "muscle_groups": ["shoulders"],
        "equipment": ["dumbbells"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Face Pull",
        "description": "Cable face pull. Pull rope to face, external rotation at end.",
        "category": "isolation",
        "muscle_groups": ["rear_delts", "upper_back"],
        "equipment": ["cable_machine", "rope_attachment"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Tricep Extension",
        "description": "Cable or dumbbell tricep extension. Full elbow extension.",
        "category": "isolation",
        "muscle_groups": ["triceps"],
        "equipment": ["cable_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Bicep Curl",
        "description": "Standing barbell or dumbbell bicep curl. Keep elbows stationary.",
        "category": "isolation",
        "muscle_groups": ["biceps"],
        "equipment": ["dumbbells"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Hammer Curl",
        "description": "Dumbbell hammer curl with neutral grip. Targets brachialis.",
        "category": "isolation",
        "muscle_groups": ["biceps", "forearms"],
        "equipment": ["dumbbells"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Cable Fly",
        "description": "Cable fly for chest. Keep slight elbow bend, squeeze at center.",
        "category": "isolation",
        "muscle_groups": ["chest"],
        "equipment": ["cable_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Lat Pulldown",
        "description": "Cable lat pulldown. Pull bar to upper chest, squeeze shoulder blades.",
        "category": "isolation",
        "muscle_groups": ["back", "biceps"],
        "equipment": ["cable_machine", "lat_bar"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 90,
    },
]

# Lower Body Accessories
LOWER_ACCESSORIES = [
    {
        "name": "Leg Press",
        "description": "Machine leg press. Full range of motion, knees track over toes.",
        "category": "isolation",
        "muscle_groups": ["quadriceps", "glutes"],
        "equipment": ["leg_press_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 120,
    },
    {
        "name": "Bulgarian Split Squat",
        "description": "Rear foot elevated split squat. Great for single-leg strength.",
        "category": "compound",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        "equipment": ["dumbbells", "bench"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 90,
        "is_bilateral": False,
    },
    {
        "name": "Walking Lunge",
        "description": "Walking lunges with bodyweight or dumbbells. Step and drop back knee.",
        "category": "compound",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        "equipment": ["dumbbells"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 90,
    },
    {
        "name": "Leg Curl",
        "description": "Machine leg curl. Isolates hamstrings.",
        "category": "isolation",
        "muscle_groups": ["hamstrings"],
        "equipment": ["leg_curl_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Leg Extension",
        "description": "Machine leg extension. Isolates quadriceps.",
        "category": "isolation",
        "muscle_groups": ["quadriceps"],
        "equipment": ["leg_extension_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Calf Raise",
        "description": "Standing or seated calf raise. Full stretch and contraction.",
        "category": "isolation",
        "muscle_groups": ["calves"],
        "equipment": ["calf_raise_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Glute Bridge",
        "description": "Barbell or bodyweight glute bridge. Squeeze glutes at top.",
        "category": "isolation",
        "muscle_groups": ["glutes", "hamstrings"],
        "equipment": ["barbell", "bench"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Hip Thrust",
        "description": "Barbell hip thrust with back on bench. Peak glute exercise.",
        "category": "isolation",
        "muscle_groups": ["glutes", "hamstrings"],
        "equipment": ["barbell", "bench", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 90,
    },
    {
        "name": "Goblet Squat",
        "description": "Dumbbell or kettlebell goblet squat. Great for learning squat pattern.",
        "category": "compound",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["dumbbell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 90,
    },
]

# Conditioning Exercises
CONDITIONING = [
    {
        "name": "Kettlebell Swing",
        "description": "Russian kettlebell swing to eye level. Hip hinge movement, explosive.",
        "category": "cardio",
        "muscle_groups": ["hamstrings", "glutes", "core", "shoulders"],
        "equipment": ["kettlebell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Kettlebell Press",
        "description": "Single-arm kettlebell overhead press. Clean to rack position first.",
        "category": "compound",
        "muscle_groups": ["shoulders", "triceps", "core"],
        "equipment": ["kettlebell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 60,
        "is_bilateral": False,
    },
    {
        "name": "Kettlebell Clean",
        "description": "Single-arm kettlebell clean to rack position. Powerful hip extension.",
        "category": "cardio",
        "muscle_groups": ["full_body"],
        "equipment": ["kettlebell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 60,
        "is_bilateral": False,
    },
    {
        "name": "Kettlebell Snatch",
        "description": "Single-arm kettlebell snatch overhead in one motion. Advanced movement.",
        "category": "cardio",
        "muscle_groups": ["full_body"],
        "equipment": ["kettlebell"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "advanced",
        "default_rest_seconds": 90,
        "is_bilateral": False,
    },
    {
        "name": "Rowing Machine",
        "description": "Concept2 rower or similar. Full-body cardio. Drive with legs, finish with arms.",
        "category": "cardio",
        "muscle_groups": ["full_body"],
        "equipment": ["rowing_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
        "is_timed": True,
    },
    {
        "name": "Assault Bike",
        "description": "Air assault bike. Arms and legs together for maximum output.",
        "category": "cardio",
        "muscle_groups": ["full_body"],
        "equipment": ["assault_bike"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
        "is_timed": True,
    },
    {
        "name": "Running",
        "description": "Outdoor or treadmill running. Cardiovascular endurance.",
        "category": "cardio",
        "muscle_groups": ["legs", "cardiovascular"],
        "equipment": ["treadmill"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
        "is_timed": True,
    },
    {
        "name": "Sled Push",
        "description": "Prowler/sled push. Low handles for leg drive, high handles for conditioning.",
        "category": "cardio",
        "muscle_groups": ["legs", "core"],
        "equipment": ["sled", "plates"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 120,
    },
    {
        "name": "Battle Ropes",
        "description": "Battle rope waves or slams. High-intensity upper body conditioning.",
        "category": "cardio",
        "muscle_groups": ["shoulders", "arms", "core"],
        "equipment": ["battle_ropes"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
        "is_timed": True,
    },
    {
        "name": "Box Jump",
        "description": "Plyometric box jump. Land softly, full hip extension at top.",
        "category": "cardio",
        "muscle_groups": ["legs", "glutes"],
        "equipment": ["plyo_box"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 90,
    },
]

# Core and Mobility
CORE_MOBILITY = [
    {
        "name": "Plank",
        "description": "Front plank. Maintain neutral spine, squeeze glutes.",
        "category": "mobility",
        "muscle_groups": ["core", "shoulders"],
        "equipment": [],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
        "is_timed": True,
    },
    {
        "name": "Side Plank",
        "description": "Side plank on elbow or hand. Stack hips and shoulders.",
        "category": "mobility",
        "muscle_groups": ["core", "obliques"],
        "equipment": [],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
        "is_timed": True,
        "is_bilateral": False,
    },
    {
        "name": "Dead Bug",
        "description": "Dead bug core exercise. Opposite arm and leg extension.",
        "category": "mobility",
        "muscle_groups": ["core"],
        "equipment": [],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Bird Dog",
        "description": "Bird dog on hands and knees. Extend opposite arm and leg.",
        "category": "mobility",
        "muscle_groups": ["core", "lower_back"],
        "equipment": [],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Pallof Press",
        "description": "Cable pallof press. Anti-rotation core exercise.",
        "category": "isolation",
        "muscle_groups": ["core", "obliques"],
        "equipment": ["cable_machine"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
    {
        "name": "Ab Wheel Rollout",
        "description": "Ab wheel rollout from knees or toes. Control the return.",
        "category": "isolation",
        "muscle_groups": ["core", "shoulders"],
        "equipment": ["ab_wheel"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "advanced",
        "default_rest_seconds": 90,
    },
    {
        "name": "Hanging Leg Raise",
        "description": "Hanging knee or straight leg raise. Control the swing.",
        "category": "isolation",
        "muscle_groups": ["core", "hip_flexors"],
        "equipment": ["pull_up_bar"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "intermediate",
        "default_rest_seconds": 60,
    },
    {
        "name": "Russian Twist",
        "description": "Seated Russian twist with weight. Rotate torso side to side.",
        "category": "isolation",
        "muscle_groups": ["core", "obliques"],
        "equipment": ["dumbbell", "medicine_ball"],
        "is_global": True,
        "is_verified": True,
        "difficulty_level": "beginner",
        "default_rest_seconds": 60,
    },
]


async def seed_exercises():
    """Seed the exercises library with default global exercises."""

    # Combine all exercise lists
    all_exercises = (
        COMPOUND_LIFTS +
        UPPER_ACCESSORIES +
        LOWER_ACCESSORIES +
        CONDITIONING +
        CORE_MOBILITY
    )

    async with AsyncSessionLocal() as db:
        try:
            # Check if exercises already exist
            result = await db.execute(select(Exercise).where(Exercise.is_global == True))
            existing_exercises = result.scalars().all()

            if existing_exercises:
                print(f"ℹ️  Found {len(existing_exercises)} existing global exercises")
                print("   Skipping seed to avoid duplicates")
                return

            # Create exercises
            exercises_created = 0
            for exercise_data in all_exercises:
                # Create exercise with UUID
                exercise = Exercise(
                    id=uuid.uuid4(),
                    **exercise_data
                )
                db.add(exercise)
                exercises_created += 1

            # Commit all exercises
            await db.commit()

            print(f"✅ Successfully seeded {exercises_created} exercises:")
            print(f"   - {len(COMPOUND_LIFTS)} compound lifts")
            print(f"   - {len(UPPER_ACCESSORIES)} upper body accessories")
            print(f"   - {len(LOWER_ACCESSORIES)} lower body accessories")
            print(f"   - {len(CONDITIONING)} conditioning exercises")
            print(f"   - {len(CORE_MOBILITY)} core/mobility exercises")

        except Exception as e:
            print(f"❌ Error seeding exercises: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_exercises())
