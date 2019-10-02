create table file_index
(
	ID int auto_increment
		primary key,
	GUID varchar(150) not null,
	JobID varchar(30),
	FileSize double,
	Timestamp double,
	FrontendUsername varchar(30),
	InstanceName varchar(30),
	EntryName varchar(30),
	FilePath varchar(150),
	MasterLog boolean,
	StartdLog boolean,
	StarterLog boolean,
	StartdHistLog boolean,
	XML_desc boolean
);
