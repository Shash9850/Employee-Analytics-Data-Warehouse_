
-- 1. Add New Employee


DROP PROCEDURE IF EXISTS sp_add_employee;

DELIMITER $$

CREATE PROCEDURE sp_add_employee (
    IN p_employee_id VARCHAR(20),
    IN p_first_name VARCHAR(100),
    IN p_last_name VARCHAR(100),
    IN p_email VARCHAR(150),
    IN p_gender VARCHAR(20),
    IN p_age INT,
    IN p_department_id INT,
    IN p_job_role VARCHAR(100),
    IN p_education_field VARCHAR(100),
    IN p_job_level INT,
    IN p_monthly_income INT,
    IN p_daily_rate INT,
    IN p_hourly_rate INT,
    IN p_business_travel VARCHAR(50),
    IN p_distance_from_home INT,
    IN p_job_involvement INT,
    IN p_job_satisfaction INT,
    IN p_environment_satisfaction INT,
    IN p_relationship_satisfaction INT,
    IN p_performance_rating INT,
    IN p_percent_salary_hike INT,
    IN p_overtime VARCHAR(10),
    IN p_marital_status VARCHAR(50),
    IN p_stock_option_level INT,
    IN p_total_working_years INT,
    IN p_years_at_company INT,
    IN p_years_in_current_role INT,
    IN p_years_since_last_promotion INT,
    IN p_years_with_current_manager INT,
    IN p_training_times_last_year INT,
    IN p_work_life_balance INT,
    IN p_num_companies_worked INT,
    IN p_attrition VARCHAR(10),
    IN p_hire_date DATE
)
BEGIN

    INSERT INTO employees (
        employee_id,
        first_name,
        last_name,
        email,
        gender,
        age,
        department_id,
        job_role,
        education_field,
        job_level,
        monthly_income,
        daily_rate,
        hourly_rate,
        business_travel,
        distance_from_home,
        job_involvement,
        job_satisfaction,
        environment_satisfaction,
        relationship_satisfaction,
        performance_rating,
        percent_salary_hike,
        overtime,
        marital_status,
        stock_option_level,
        total_working_years,
        years_at_company,
        years_in_current_role,
        years_since_last_promotion,
        years_with_current_manager,
        training_times_last_year,
        work_life_balance,
        num_companies_worked,
        attrition,
        hire_date
    )
    VALUES (
        p_employee_id,
        p_first_name,
        p_last_name,
        p_email,
        p_gender,
        p_age,
        p_department_id,
        p_job_role,
        p_education_field,
        p_job_level,
        p_monthly_income,
        p_daily_rate,
        p_hourly_rate,
        p_business_travel,
        p_distance_from_home,
        p_job_involvement,
        p_job_satisfaction,
        p_environment_satisfaction,
        p_relationship_satisfaction,
        p_performance_rating,
        p_percent_salary_hike,
        p_overtime,
        p_marital_status,
        p_stock_option_level,
        p_total_working_years,
        p_years_at_company,
        p_years_in_current_role,
        p_years_since_last_promotion,
        p_years_with_current_manager,
        p_training_times_last_year,
        p_work_life_balance,
        p_num_companies_worked,
        p_attrition,
        p_hire_date
    );

    -- Create initial SCD2 record in the warehouse dimension
    INSERT INTO dim_employee (
        employee_id,
        first_name,
        last_name,
        email,
        gender,
        age,
        department_id,
        job_role,
        education_field,
        job_level,
        monthly_income,
        daily_rate,
        hourly_rate,
        business_travel,
        distance_from_home,
        job_involvement,
        job_satisfaction,
        environment_satisfaction,
        relationship_satisfaction,
        performance_rating,
        percent_salary_hike,
        overtime,
        marital_status,
        stock_option_level,
        total_working_years,
        years_at_company,
        years_in_current_role,
        years_since_last_promotion,
        years_with_current_manager,
        training_times_last_year,
        work_life_balance,
        num_companies_worked,
        attrition,
        hire_date,
        effective_start_date,
        effective_end_date,
        is_current
    )
    SELECT
        e.employee_id,
        e.first_name,
        e.last_name,
        e.email,
        e.gender,
        e.age,
        e.department_id,
        e.job_role,
        e.education_field,
        e.job_level,
        e.monthly_income,
        e.daily_rate,
        e.hourly_rate,
        e.business_travel,
        e.distance_from_home,
        e.job_involvement,
        e.job_satisfaction,
        e.environment_satisfaction,
        e.relationship_satisfaction,
        e.performance_rating,
        e.percent_salary_hike,
        e.overtime,
        e.marital_status,
        e.stock_option_level,
        e.total_working_years,
        e.years_at_company,
        e.years_in_current_role,
        e.years_since_last_promotion,
        e.years_with_current_manager,
        e.training_times_last_year,
        e.work_life_balance,
        e.num_companies_worked,
        e.attrition,
        e.hire_date,
        e.hire_date,
        '9999-12-31',
        1
    FROM employees e
    WHERE e.employee_id = p_employee_id;

END$$

DELIMITER ;



-- 2. Update Employee Department - SCD Type 2


DROP PROCEDURE IF EXISTS sp_update_employee_department;

DELIMITER $$

CREATE PROCEDURE sp_update_employee_department (
    IN p_employee_id VARCHAR(20),
    IN p_new_department_id INT,
    IN p_change_date DATE
)
BEGIN

    DECLARE v_current_sk BIGINT;
    DECLARE v_old_department_id INT;

    -- Find current employee dimension record
    SELECT
        employee_sk,
        department_id
    INTO
        v_current_sk,
        v_old_department_id
    FROM dim_employee
    WHERE employee_id = p_employee_id
      AND is_current = 1
    LIMIT 1;

    -- Close existing SCD2 record
    UPDATE dim_employee
    SET
        effective_end_date = DATE_SUB(p_change_date, INTERVAL 1 DAY),
        is_current = 0
    WHERE employee_id = p_employee_id
      AND is_current = 1;

    -- Create new SCD2 version
    INSERT INTO dim_employee (
        employee_id,
        first_name,
        last_name,
        email,
        gender,
        age,
        department_id,
        job_role,
        education_field,
        job_level,
        monthly_income,
        daily_rate,
        hourly_rate,
        business_travel,
        distance_from_home,
        job_involvement,
        job_satisfaction,
        environment_satisfaction,
        relationship_satisfaction,
        performance_rating,
        percent_salary_hike,
        overtime,
        marital_status,
        stock_option_level,
        total_working_years,
        years_at_company,
        years_in_current_role,
        years_since_last_promotion,
        years_with_current_manager,
        training_times_last_year,
        work_life_balance,
        num_companies_worked,
        attrition,
        hire_date,
        effective_start_date,
        effective_end_date,
        is_current
    )
    SELECT
        employee_id,
        first_name,
        last_name,
        email,
        gender,
        age,
        p_new_department_id,
        job_role,
        education_field,
        job_level,
        monthly_income,
        daily_rate,
        hourly_rate,
        business_travel,
        distance_from_home,
        job_involvement,
        job_satisfaction,
        environment_satisfaction,
        relationship_satisfaction,
        performance_rating,
        percent_salary_hike,
        overtime,
        marital_status,
        stock_option_level,
        total_working_years,
        years_at_company,
        years_in_current_role,
        years_since_last_promotion,
        years_with_current_manager,
        training_times_last_year,
        work_life_balance,
        num_companies_worked,
        attrition,
        hire_date,
        p_change_date,
        '9999-12-31',
        1
    FROM dim_employee
    WHERE employee_sk = v_current_sk;

    -- Update OLTP employee's current department
    UPDATE employees
    SET department_id = p_new_department_id
    WHERE employee_id = p_employee_id;

END$$

DELIMITER ;



-- 3. Assign Employee to Project


DROP PROCEDURE IF EXISTS sp_assign_employee_to_project;

DELIMITER $$

CREATE PROCEDURE sp_assign_employee_to_project (
    IN p_employee_id VARCHAR(20),
    IN p_project_id INT,
    IN p_allocation_percent INT,
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    DECLARE v_assignment_id INT;

    SELECT COALESCE(MAX(assignment_id), 0) + 1
    INTO v_assignment_id
    FROM employee_projects;

    INSERT INTO employee_projects (
        assignment_id,
        employee_id,
        project_id,
        allocation_percent,
        start_date,
        end_date
    )
    VALUES (
        v_assignment_id,
        p_employee_id,
        p_project_id,
        p_allocation_percent,
        p_start_date,
        p_end_date
    );

END$$

DELIMITER ;


-- 4. Add Performance Review


DROP PROCEDURE IF EXISTS sp_add_performance_review;

DELIMITER $$

CREATE PROCEDURE sp_add_performance_review (
    IN p_employee_id VARCHAR(20),
    IN p_review_date DATE,
    IN p_review_period VARCHAR(20),
    IN p_performance_score DECIMAL(5,2),
    IN p_performance_rating INT,
    IN p_manager_rating INT,
    IN p_employee_rating INT,
    IN p_comments VARCHAR(500)
)
BEGIN

    INSERT INTO performance_reviews (
        employee_id,
        review_date,
        review_period,
        performance_score,
        performance_rating,
        manager_rating,
        employee_rating,
        comments
    )
    VALUES (
        p_employee_id,
        p_review_date,
        p_review_period,
        p_performance_score,
        p_performance_rating,
        p_manager_rating,
        p_employee_rating,
        p_comments
    );

END$$

DELIMITER ;

SHOW PROCEDURE STATUS
WHERE Db = 'employee_analytics_dw';




-- 5. Create Project


DROP PROCEDURE IF EXISTS sp_add_project;

DELIMITER $$

CREATE PROCEDURE sp_add_project (
    IN p_project_id INT,
    IN p_project_name VARCHAR(255),
    IN p_department_id INT,
    IN p_start_date DATE,
    IN p_end_date DATE,
    IN p_budget DECIMAL(15,2),
    IN p_status VARCHAR(50)
)
BEGIN

    INSERT INTO projects (
        project_id,
        project_name,
        department_id,
        start_date,
        end_date,
        budget,
        status
    )
    VALUES (
        p_project_id,
        p_project_name,
        p_department_id,
        p_start_date,
        p_end_date,
        p_budget,
        p_status
    );

END$$

DELIMITER ;
