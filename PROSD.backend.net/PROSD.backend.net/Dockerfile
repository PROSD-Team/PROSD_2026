# --- Build stage ---
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy csproj first → restore → then copy code
COPY ["PROSD.backend.net.csproj", "./"]
RUN dotnet restore "PROSD.backend.net.csproj"

COPY . .
RUN dotnet build "PROSD.backend.net.csproj" -c Release -o /app/build

# --- Publish stage ---
FROM build AS publish
RUN dotnet publish "PROSD.backend.net.csproj" -c Release -o /app/publish /p:UseAppHost=false

# --- Runtime stage ---
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
COPY --from=publish /app/publish .

# Use non-root user
USER app

EXPOSE 80
EXPOSE 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/health || exit 1

ENTRYPOINT ["dotnet", "PROSD.backend.net.dll"]