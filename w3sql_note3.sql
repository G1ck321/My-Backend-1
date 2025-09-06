




to change the datatype of column alter table table_name 
modify columnname datatype


SQL JOIN An SQL JOIN clause is used to combine rows from two or more tables,
based on a common field between them.
The most common type of join is: SQL INNER JOIN(simple join).An SQL INNER JOIN
returns all rows from multiple tables where the join condition is met
SELECT table1.OrderID, table2.CustomerName, table1.OrderDate
FROM table1
INNER JOIN table2
ON table1.CustomerID=table2.CustomerID; 
join is also inner join
left join returns from the left condition of the = even if the right does not match
right join from the right.

mysql does not support full outer join you do a union
SELECT Customers.CustomerName, Orders.OrderID FROM Customers
LEFT JOIN Orders ON Customers.CustomerID=Orders.CustomerID
union
SELECT Customers.CustomerName, Orders.OrderID FROM Customers
right JOIN Orders ON Customers.CustomerID=Orders.CustomerID

places them aftereach other eg. names
SELECT column_name(s) FROM table1
UNION--- union all selects all (duplicate values also)
SELECT column_name(s) FROM table2;

you can create a table in another db and copy the info from a db into into
create table db2.table
select * from db1.table;
to edit
insert into db2.table
select * from db1.table-- you can specify the columns but the table must match

to edit a column in db2 with data from db1
update db2
set db2.column = (select column from db1.table where column = db1.val)

INSERT INTO table_name (column1,column2,column3,...)
VALUES (value1,value2,value3,...);--they can be in anny order;

CREATE TABLE Persons
(
PersonID int,
LastName varchar(255),
FirstName varchar(255),
Address varchar(255),
City varchar(255)
); 
If you try to use null to catch a query it will not work oo because null does not exist use is next time
update table
join db1.column  on table.id = table.column.id
set table.column = db1.column.field;
