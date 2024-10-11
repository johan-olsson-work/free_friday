# Some ideas of how to continue

Might spend at most one more Friday on this so everything might not be done, but some ideas at least...

1. Update the Hello World to something that states it's current version and a timestamp in the log whenever it is updated
2. Update the ACAP_updater
   - remove initial VAPIX example stuff that is not needed from the ACAP_updater
   - Rename the application (still called vapix_example)
   - refactor the README.md to at least contain something about what is done
   - Make it run continuously looking for a new .eap file to run upload.cgi for
   - Make it possible to use different locations for the .eap files. E.g. add a parameter so that the .eap file path can be set in settings of the ACAP
3. Add the chrashacap from Jan F to the mix, this probably demands some refactoring of the test script to get good data from.
4. Create some way of recording the results when running long sessions, e.g. over night.
5. Create instructions on how to set it up
6. ...
