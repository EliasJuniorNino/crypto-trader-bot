APP_NAME=app
BUILD_DIR=build

.PHONY: build

build:
	mkdir -p $(BUILD_DIR)
	go build -o $(BUILD_DIR)/$(APP_NAME) .
	
build-linux:
	mkdir -p $(BUILD_DIR)
	CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build -o $(BUILD_DIR)/$(APP_NAME)-linux .

build-win:
	mkdir -p $(BUILD_DIR)
	CGO_ENABLED=1 GOOS=windows GOARCH=amd64 CC=x86_64-w64-mingw32-gcc go build -o $(BUILD_DIR)/$(APP_NAME)-win_x86_64.exe .

build-macos:
	mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build -o $(BUILD_DIR)/$(APP_NAME)-macos .

build-silicon:
	mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build -o $(BUILD_DIR)/$(APP_NAME)-silicon .

clean:
	rm -rf $(BUILD_DIR)
