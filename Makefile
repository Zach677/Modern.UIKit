SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

ROOT_DIR := $(shell pwd)
PROJECT := $(ROOT_DIR)/ModernUIKit.xcodeproj
SCHEME := ModernUIKit
CONFIGURATION ?= Debug
DERIVED_DATA ?= $(ROOT_DIR)/.DerivedData
SIMULATOR_DESTINATION := generic/platform=iOS Simulator
DEVICE_DESTINATION := generic/platform=iOS

XCODEBUILD := xcodebuild \
	-project "$(PROJECT)" \
	-scheme "$(SCHEME)" \
	-configuration "$(CONFIGURATION)" \
	-derivedDataPath "$(DERIVED_DATA)"

.PHONY: help build build-sim build-device test clean

help:
	@echo "Targets:"
	@echo "  build         Alias for build-sim"
	@echo "  build-sim     Build the app for iOS Simulator"
	@echo "  build-device  Build the app for a generic iOS device"
	@echo "  test          Run the hosted unit tests on an available iPhone simulator"
	@echo "  clean         Remove derived data"

build: build-sim

build-sim:
	$(XCODEBUILD) \
		-destination "$(SIMULATOR_DESTINATION)" \
		CODE_SIGNING_ALLOWED=NO \
		CODE_SIGNING_REQUIRED=NO \
		CODE_SIGN_IDENTITY="" \
		build

build-device:
	$(XCODEBUILD) \
		-destination "$(DEVICE_DESTINATION)" \
		build

test:
	@TEST_DESTINATION="$${TEST_DESTINATION:-$$(python3 ./scripts/resolve_test_destination.py)}"; \
	echo "Using test destination: $$TEST_DESTINATION"; \
	$(XCODEBUILD) \
		-destination "$$TEST_DESTINATION" \
		CODE_SIGNING_ALLOWED=NO \
		CODE_SIGNING_REQUIRED=NO \
		CODE_SIGN_IDENTITY="" \
		test

clean:
	rm -rf "$(DERIVED_DATA)"
