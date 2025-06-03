package dto

import "app/src/models"

type AlternativeAPIResponse struct {
	Data []models.AlternativeFearData `json:"data"`
}
