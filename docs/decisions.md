1- Separate Postgres containers vs one container with 3 isolated DBs?

i went with seperate containers per service. this way the DBs are not relying on each other. no single point of failure. difficult to manage as a bigginer, but from learning perspective i'll get to learn about inter-containers connections. also, a single DB for all microservices kills the main point of having MSs. (i read about connection poolers (pgbouncer) for limited connection at a time to db per service.)

2- Monorepo vs polyrepo?

i chose to store the MSs in a monorepo. polyrepos are difficult manage. plus the current project is a short assignment. within the monorepo i have kept the dockerfiles for each service seperat. a single shared docker-compose will setup everything instead of setting up each MS in a seperate repo and it will also make inter-service networking easy as all the containers are on the same docker network here. decreases project setup overhead.

3- Why these 3 services? Why is appointments a future 4th and not inside patient-service?

for starting i think 3 services would be enough for hands on practice. appointments have their own different flows so it should have its own MS. also it is not only connected to patient, the provider also has a relation with it. also, this will contain scheduling logic (temporal workflow) and it can be scaled, replaced and restarted independently without modyfying patient opr procider data.

4- Is a patient a user? Patient has user_id but no FK across DBs, how do you keep it consistent?

yes, a patient is a user. any person/account using the smart health system has to go through auth first and w.r.t. that everyone is a user. the user_id in patient is in refrence to the id in auth table. since the DBs of both these services are isolated, in this case i will be trustung the jwt. when a patient creation request will comes, teh jwt will already prove that the user exists (auth service issues the jwt). the user id will be extracted from the jwt and stored in patient tabble against that patient.

5- Double-booking prevention, unique constraint on (provider_id, start_time) in slots table,  why is that better than an if slot_taken check in code?

the unique constrait will terminate the query as soon as the commit is initiated, an error will be thrown. it will avoid race condition. also the slot_taken check would required me to loop throgh all the slots and compare client and slot strat time of each record to the newly added one, increasing execution time and complexity.

6- Appointment state machine: ![alt text](IMG_0213.jpeg)

7- DB schema: ![alt text](IMG_0208.jpeg)

8- transitions for appointment status
requested -> confirmed / cancelled / failed
confirmed -> checked_in / cancelled / no_show
checked_in -> in_progress / cancelled
in_progress -> completed / cancelled

9- why kafka for appointment events and not direct HTTP calls between services?

appointment-service doesnt need to know who is consuming its events. if i used direct HTTP, appointment-service would have to call analytics-service explicitly, which creates tight coupling. if analytics goes down, the appointment call fails too. with kafka, appointment-service just publishes to a topic and moves on. analytics-service consumes whenever it's ready. also if i later want another service to react to appointment events, i just add another consumer, no changes needed in appointment-service.

10- why celery + rabbitmq for notifications and not temporal?

temporal is for workflows that need durability, rollback, and retry with state. notifications are fire-and-forget, they dont need all that. if a notification fails it doesnt mean i should undo the appointment or user creation. celery with rabbitmq is a much simpler and lighter fit here. i also didnt want to mix notification logic into the workflow itself because that would make rollback decisions more complicated (should a WF roll back because an email wasnt sent? no.). so i kept them separate and just dispatch a celery task at the end of each workflow.

11- why redis for analytics counters and not querying the DB directly?

the analytics endpoint would be hit frequently. if i queried the DB every time for total appointments, completions etc. it would be slow and put load on the DB. redis keeps these as in-memory counters (incr) so reads are O(1). i update the counters from the kafka consumer as events come in, so the data is always up to date without a single DB query on the analytics endpoint. the only exception is total_patients which comes from a kafka event too (patient.created) so same pattern applies.

12- why not call patient-service directly from analytics-service to get total patients?

inter-service HTTP calls create runtime coupling. if patient-service is down, analytics breaks too. also it goes against the event-driven architecture we already have. instead patient-service publishes a patient.created kafka event when a patient is registered, and analytics-service increments a redis counter from that. analytics never needs to know patient-service exists.

13- why use temporal for user creation and not just doing everything in the auth-service endpoint?

the user creation flow touches multiple services: auth, patient, provider. if any of these fail midway the system ends up in an inconsistent state. temporal handles this with activity retries and a compensation (rollback) pattern. if patient record creation fails, temporal automatically runs the cleanup activities to delete whatever was created and fail the user. doing this in a single HTTP handler would mean writing manual rollback logic in the endpoint, and if the server crashes mid-way there is no recovery. temporal persists workflow state so it can resume even after a crash.

14- why opentelemetry + jaeger and not just logging?

logs tell me what happened in one service. jaeger shows me the full journey of a request across all services with timings. for example if a user creation request is slow, logs in auth-service wont tell me if the delay is in the temporal activity, the patient-service call, or the DB. jaeger shows the entire trace as a waterfall so i can pinpoint exactly where time is being spent. opentelemetry is the standard library for instrumentation and jaeger is just the backend that receives and displays the traces.

15- orphan data across services, what happens if a user is deleted but their patient/provider record still exists?

since each service has its own DB there are no cross-DB foreign keys. if a user is deleted from auth-service, the patient and provider records in their respective DBs still have that user_id with nothing to reference. this is called orphan data and it is a real consistency problem in microservices.
the fix i would implement is soft deletes with role-aware cleanup. there are two separate cases:
    case 1: patient or provider record is deleted: this does not mean the user is gone. a user can have multiple roles. if a patient record is deleted, i just remove the patient role from the user in auth-service (PATCH /users/{id}/remove_roles already exists). same for provider. the user stays active and can still hold other roles like fd_staff or admin. no is_deleted needed on the user.
    case 2: the user itself is deleted: this is where orphan data actually happens. i would add is_deleted to the patients and providers tables and set status = 'deleted' on the user in auth. when a user is deleted, auth-service publishes a user.deleted kafka event. patient-service and provider-service consume it and set is_deleted = true on matching records. appointment-service also consumes it and cancels any active appointments for that patient or provider.
medical records should not be physically deleted for audit and legal reasons, so soft delete is the right approach regardless.