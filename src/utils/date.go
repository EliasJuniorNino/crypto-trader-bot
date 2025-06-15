package utils

import "time"

func StartOfCurrentDayUTC() time.Time {
	t := time.Now().UTC().Add(-1 * time.Hour)
	return time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, time.UTC)
}
