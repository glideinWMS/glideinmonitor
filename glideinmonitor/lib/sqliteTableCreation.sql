CREATE TABLE "file_index"
(
	ID INTEGER
		constraint file_index_pk
			primary key autoincrement,
	GUID varchar NOT NULL,
	JobID varchar,
	FileSize double,
	Timestamp timestamp,
	FrontendUsername varchar,
	InstanceName varchar,
	EntryName varchar,
	FilePathOriginal varchar,
	FilePathFilter varchar,
	MasterLog boolean,
	StartdLog boolean,
	StarterLog boolean,
	StartdHistLog boolean,
	XML_desc boolean
);

create unique index file_index_GUID_uindex
    on file_index (GUID);
