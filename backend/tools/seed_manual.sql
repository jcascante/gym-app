PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
INSERT INTO programs (name, description, program_type, builder_type, algorithm_version, input_data, calculated_data, is_template, is_default, is_public, template_version, required_parameters, optional_parameters, tags, goals, times_assigned, duration_weeks, days_per_week, id, created_at, created_by, updated_at, updated_by) VALUES (Template Seed 1,Linear progression seed,strength_linear,strength_linear_5x5,v1.0.0,{"builder_type": "strength_linear_5x5", "name": "Seed 5x5", "movements": [{"name": "Squat", "one_rm": 300.0}], "duration_weeks": 4, "days_per_week": 3, "is_template": true},{},1,0,0,1,[],[],[],[],0,4,3,11111111-1111-1111-1111-111111111111, datetime("now"), NULL, datetime("now"), NULL);
COMMIT;
PRAGMA foreign_keys=ON;
