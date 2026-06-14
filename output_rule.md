filter: 
  operation: each filter has operation, including eq, neq, gt, lt, contains
  1. location can be used for team or event, will be flatten like this: 
    team.city, team.postcode, team.country, team.region
    event.city, event.postcode, event.country, event.region, event.venue
    city, postcode, country, use eq, region and venue use contains
  2. event: event.name, event.sku
     event.name is contains, sku use eq
  3. time: can be event time or match time
    event.starttime, match.time, match.startTime, 
    time is 
