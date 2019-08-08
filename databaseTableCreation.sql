CREATE TABLE "file_index"
(
	ID INTEGER
		constraint file_index_pk
			primary key autoincrement,
	JobID varchar,
	FileSize double,
	Timestamp timestamp,
	FrontendUsername varchar,
	InstanceName varchar,
	EntryName varchar,
	FilePath varchar,
	MasterLog boolean,
	StartdLog boolean,
	StarterLog boolean,
	StartdHistLog boolean,
	XML_desc boolean
)

