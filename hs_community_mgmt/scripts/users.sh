./hsctl managepy access_user test1 create --first=test1 --last=nick --email=test1@test.com
./hsctl managepy access_user test2 create --first=test2 --last=nick --email=test2@test.com
./hsctl managepy access_user test3 create --first=test3 --last=nick --email=test3@test.com
./hsctl managepy access_user test4 create --first=test4 --last=nick --email=test4@test.com
./hsctl managepy access_user test5 create --first=test5 --last=nick --email=test5@test.com
./hsctl managepy access_user test6 create --first=test6 --last=nick --email=test6@test.com
./hsctl managepy access_user test7 create --first=test7 --last=nick --email=test7@test.com
./hsctl managepy access_user test8 create --first=test8 --last=nick --email=test8@test.com
./hsctl managepy access_user test9 create --first=test9 --last=nick --email=test9@test.com
./hsctl managepy access_user test10 create --first=test10 --last=nick --email=test10@test.com
./hsctl managepy access_user test11 create --first=test11 --last=nick --email=test11@test.com
./hsctl managepy access_user test12 create --first=test12 --last=nick --email=test12@test.com
./hsctl managepy access_group demo create --description=doo --purpose=doo --owner=test10
./hsctl managepy access_group lition create --description=doo --purpose=doo --owner=test2
./hsctl managepy access_group Friends create --description=dodo --purpose=bird --owner=test4
./hsctl managepy access_group Family create --description=dodo --purpose=bird --owner=test3
./hsctl managepy access_group drop create --description=doo --purpose=doo --owner=test1
./hsctl managepy access_group down create --description=doo --purpose=doo --owner=test1
./hsctl managepy access_group doom create --description=doo --purpose=doo --owner=test5
./hsctl managepy access_group disallow create --description=doo --purpose=doo --owner=test6
./hsctl managepy access_community octopi create --description=doo --purpose=doo --owner=test1
./hsctl managepy access_community octopi group Family request
./hsctl managepy access_community octopi group Friends request
./hsctl managepy access_community octopi group demo request
./hsctl managepy access_community octopi group lition request
./hsctl managepy access_community octopi group drop request
./hsctl managepy access_community octopi group down request
./hsctl managepy access_community octopi group doom request
./hsctl managepy access_community octopi group disallow request
./hsctl managepy access_community octopi group disallow decline
./hsctl managepy access_community octopi group doom decline
