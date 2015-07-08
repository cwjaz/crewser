PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
INSERT INTO "auth_user" VALUES(2,'pbkdf2_sha256$15000$MATqypMxp8n4$0snjL3CP2rrQ2xdSCT7fN+77dOXfD1RETmbxpsjtP5Q=','2015-07-08 09:05:24.431228',0,'test','','','',1,1,'2015-07-08 09:04:54');
INSERT INTO "auth_user" VALUES(3,'pbkdf2_sha256$15000$2WGsECjl3Tm1$YeCi21ko6cW1rzRFf1qrrhCbGTx7W0GRBn1DLSvXEyc=','2015-07-08 09:15:37.646404',0,'test2','','','',1,1,'2015-07-08 09:05:15.782988');
INSERT INTO "auth_user_groups" VALUES(3,2,1);
INSERT INTO "auth_user_groups" VALUES(4,2,2);
INSERT INTO "auth_user_groups" VALUES(5,3,2);
INSERT INTO "crewdb_company" VALUES(1,'Baufirma','0223221222','baufirma@inter.net','Brauereistrasse 12
18223 Bautzen
Deutschland');
INSERT INTO "crewdb_company" VALUES(2,'Getränkeservice','03812828339','drink@home.de','Servicestrasse 23
11111 Großstadt
Deutschland');
INSERT INTO "crewdb_crew" VALUES(1,'Baucrew',200,'',0,2);
INSERT INTO "crewdb_crew" VALUES(2,'Partycrew',NULL,'',1,3);
INSERT INTO "crewdb_worktime" VALUES(1,'2015-06-09','2015-07-22','',2);
INSERT INTO "crewdb_service" VALUES(1,'aufräumen',NULL);
INSERT INTO "crewdb_service" VALUES(2,'bauleitung',5);
INSERT INTO "crewdb_service" VALUES(3,'schulung',4);
INSERT INTO "crewdb_member" VALUES(1,'Bob Baumeister','03812222222','bob@baumeister.test','Baumarktstrasse 12
10222 Bautzen',1,0,3,1);
INSERT INTO "crewdb_member" VALUES(2,'Tina','','tina@baucrew.org','',0,0,3,1);
INSERT INTO "crewdb_member" VALUES(3,'Sonja','','sonja@baucrew.org',NULL,0,0,3,1);
INSERT INTO "crewdb_member" VALUES(4,'Dancer','','dancer@party.mix','',1,0,NULL,2);
INSERT INTO "crewdb_compensation" VALUES(1,'',1,1);
INSERT INTO "crewdb_billing" VALUES(1,'2015-07-08',1,'Event-Organisator

Partyort
10331 Glücks-Stadt
Deutschland

USt-ID-Nr.: DE222222222','Sonja: Baucrew','Baufirma
Brauereistrasse 12
18223 Bautzen
Deutschland
Phone: 0223221222
EMail: baufirma@inter.net','32311333','1131313131','','','2015-07-08','Lieferung Gipsplatten','','2015-07-08',36.14,43,'19%, Bescheid vom Finanzamt liegt vor',0,0,1,3,1,3);
INSERT INTO "crewdb_access" VALUES(1,16,1,3);
INSERT INTO "crewdb_access" VALUES(2,8,2,1);
INSERT INTO "crewdb_access" VALUES(3,4,2,2);
COMMIT;
