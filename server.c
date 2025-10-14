/*
 * Simple TCP Server Example for RTLinux
 * Replace this with your actual server implementation
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <signal.h>

#define BUFFER_SIZE 1024
#define MAX_CONNECTIONS 5

volatile int running = 1;

void signal_handler(int signum) {
    printf("\nReceived signal %d, shutting down...\n", signum);
    running = 0;
}

int main(int argc, char *argv[]) {
    int server_fd, client_fd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len;
    char buffer[BUFFER_SIZE];
    int port;
    int opt = 1;
    int bytes_received;
    int message_count = 0;

    // Parse port from command line
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <port>\n", argv[0]);
        return 1;
    }
    port = atoi(argv[1]);

    // Setup signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    printf("=== TCP Server Starting ===\n");
    printf("Port: %d\n", port);
    printf("Max connections: %d\n", MAX_CONNECTIONS);
    printf("===========================\n\n");

    // Create socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("ERROR: Socket creation failed");
        return 1;
    }

    // Set socket options
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("ERROR: Setsockopt failed");
        close(server_fd);
        return 1;
    }

    // Configure server address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);

    // Bind socket
    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("ERROR: Bind failed");
        close(server_fd);
        return 1;
    }

    // Listen for connections
    if (listen(server_fd, MAX_CONNECTIONS) < 0) {
        perror("ERROR: Listen failed");
        close(server_fd);
        return 1;
    }

    printf("Server listening on port %d\n", port);
    printf("Waiting for connections...\n\n");

    // Accept connections (simplified - single client for demo)
    client_len = sizeof(client_addr);
    client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);

    if (client_fd < 0) {
        perror("ERROR: Accept failed");
        close(server_fd);
        return 1;
    }

    printf("Client connected from %s:%d\n",
           inet_ntoa(client_addr.sin_addr),
           ntohs(client_addr.sin_port));

    // Receive data from client
    while (running) {
        memset(buffer, 0, BUFFER_SIZE);
        bytes_received = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);

        if (bytes_received <= 0) {
            if (bytes_received == 0) {
                printf("Client disconnected\n");
            } else {
                perror("ERROR: Receive failed");
            }
            break;
        }

        message_count++;
        printf("[MSG %d] Received %d bytes: %s\n", message_count, bytes_received, buffer);

        // Echo back to client
        if (send(client_fd, buffer, bytes_received, 0) < 0) {
            perror("ERROR: Send failed");
            break;
        }
        printf("[MSG %d] Echoed back to client\n", message_count);
    }

    // Cleanup
    printf("\n=== Server Statistics ===\n");
    printf("Total messages: %d\n", message_count);
    printf("========================\n");

    close(client_fd);
    close(server_fd);

    printf("Server shutdown complete\n");
    return 0;
}
