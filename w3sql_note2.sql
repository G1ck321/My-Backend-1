select distinct columnname, column_name FROM table_name;
where operator field, some operators:
= equal to
>= Greater than or equal
<= Less than or equal
BETWEEN Between an inclusive range SELECT Columnname from table_name where other Columnname BETWEEN field and field;
LIKE Search for a pattern
IN To specify multiple possible values for a column

To specify the nuumber of dat you actually want(MYSQL and Oracle)
    select column_name 
    from table_name
    limit number;
SQL Server / MS Access Syntax
    SELECT TOP number|percent column_name(s)
    FROM table_name;

% A substitute for zero or more characters 
_ A substitute for a single character -- SELECT * FROM Customers WHERE City LIKE 'L_n_on';
[charlist] --Sets and ranges of characters to match
[^charlist] or [!charlist] Matches only a character NOT specified within the brackets

Delete from table where column_name = "field"
NULL means nothing

select * from table_name order by Ages asc or desc
SELECT TOP 2 * FROM Customers; 
SELECT TOP 50 PERCENT * FROM Customers; 

SELECT * FROM table show all rows 
WHERE col_name LIKE 's%';(field starts with "s"), %s (field ends with "s"), %a%(field contains a)
You can also do NOT LIKE. 
The "%" sign is used to define wildcards (missing letters) both before and after the pattern

IN is used to order the data 
SELECT field FROM table_name where another_col IN(val1,val2,...,valN)
Order of Syntax:
    SELECT
    FROM
    WHERE
    GROUP BY (optional)
    HAVING (optional)
    ORDER BY  (optional)
    LIMIT (optional)
You can use BETWEEN for numerical values select region from table_name where ages between 17 AND 19;
ALIAS- Gives a temporary name to a table or a column. 
    SELECT column_name AS alias_name FROM table_name; - column 
    SELECT column_name(s) FROM table_name AS alias_name;


