.PHONY: help build run stop restart logs shell clean rebuild status test

# Default target
help:
	@echo "WeasyPrint Sandbox - Docker Commands"
	@echo "===================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make build     - Build the Docker image"
	@echo "  make run       - Run the container and open browser"
	@echo "  make stop      - Stop the container"
	@echo "  make restart   - Restart the container"
	@echo "  make logs      - View container logs (follow mode)"
	@echo "  make shell     - Open a shell inside the container"
	@echo "  make status    - Show container status"
	@echo "  make test      - Run a quick test to generate PDF"
	@echo "  make rebuild   - Rebuild image and restart container"
	@echo "  make clean     - Stop and remove container and image"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make build   (first time only)"
	@echo "  2. make run     (opens browser automatically)"
	@echo "  3. Edit index.html or styles.css"
	@echo "  4. Watch live updates in browser!"
	@echo ""

# Build the Docker image
build:
	@echo "Building Docker image..."
	docker compose build

# Run the container
run:
	@echo "Starting WeasyPrint sandbox..."
	@echo "Edit index.html or styles.css to see live updates!"
	docker compose up -d
	@echo ""
	@echo "✓ Container started!"
	@echo ""
	@echo "🌐 Opening browser at http://localhost:5000"
	@echo "   If browser doesn't open, visit: http://localhost:5000"
	@echo ""
	@sleep 2
	@(command -v open > /dev/null && open http://localhost:5000) || \
	 (command -v xdg-open > /dev/null && xdg-open http://localhost:5000) || \
	 (command -v start > /dev/null && start http://localhost:5000) || \
	 echo "Please open http://localhost:5000 in your browser"

# Stop the container
stop:
	@echo "Stopping container..."
	docker compose down

# Restart the container
restart: stop run

# View logs
logs:
	@echo "Showing logs (Ctrl+C to exit)..."
	docker compose logs -f

# Open shell in container
shell:
	@echo "Opening shell in container..."
	docker compose exec weasyprint-sandbox /bin/bash

# Show container status
status:
	@echo "Container status:"
	@docker compose ps

# Test PDF generation
test:
	@echo "Testing PDF generation..."
	docker compose exec weasyprint-sandbox python3 -c "from weasyprint import HTML; HTML(filename='index.html').write_pdf('output.pdf'); print('✓ PDF generated successfully!')"

# Rebuild everything
rebuild:
	@echo "Rebuilding image and restarting..."
	docker compose down
	docker compose build --no-cache
	docker compose up -d
	@echo "✓ Rebuild complete!"

# Clean up everything
clean:
	@echo "Cleaning up..."
	docker compose down -v
	docker rmi weasyprint_sandbox-weasyprint-sandbox 2>/dev/null || true
	@echo "✓ Cleanup complete!"

# Alternative commands using docker directly (without docker compose)
build-docker:
	@echo "Building with docker..."
	docker build -t weasyprint-sandbox .

run-docker:
	@echo "Running with docker..."
	docker run -d --name weasyprint-sandbox \
		-v $(PWD)/index.html:/app/index.html \
		-v $(PWD)/styles.css:/app/styles.css \
		-v $(PWD)/output.pdf:/app/output.pdf \
		weasyprint-sandbox

stop-docker:
	@echo "Stopping docker container..."
	docker stop weasyprint-sandbox
	docker rm weasyprint-sandbox

logs-docker:
	docker logs -f weasyprint-sandbox
