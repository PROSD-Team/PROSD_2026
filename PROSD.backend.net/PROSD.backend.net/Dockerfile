FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
USER $APP_UID
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src
COPY ["PROSD.backend.net/PROSD.backend.net.csproj", "PROSD.backend.net/"]
RUN dotnet restore "./PROSD.backend.net/PROSD.backend.net.csproj"
COPY . .
WORKDIR "/src/PROSD.backend.net"
RUN dotnet build "./PROSD.backend.net.csproj" -c $BUILD_CONFIGURATION -o /app/build

FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "./PROSD.backend.net.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .

USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
USER $APP_UID

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:80/health || exit 1

ENTRYPOINT ["dotnet", "PROSD.backend.net.dll"]