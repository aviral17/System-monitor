import { useState, useEffect, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  RefreshCw,
  Download,
  Lock,
  Shield,
  Moon,
  Cpu,
  MemoryStick,
  HardDrive,
  User,
  AlertCircle,
  CheckCircle2,
  Laptop,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import axios from "axios";
import { format } from "date-fns";

const Dashboard = () => {
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [osFilter, setOsFilter] = useState("all");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get("/api/machines");
      setMachines(response.data);
      setError(null);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError("Failed to load data. Please check backend connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleExport = () => {
    window.open("/api/export", "_blank");
  };

  const getStatusBadge = (status, goodText, badText, isWarning = false) => {
    if (status) {
      return (
        <Badge className="bg-green-600 text-white">
          <CheckCircle2 className="h-4 w-4 mr-1" /> {goodText}
        </Badge>
      );
    } else if (isWarning) {
      return (
        <Badge className="bg-yellow-500 text-gray-900">
          <AlertCircle className="h-4 w-4 mr-1" /> {badText}
        </Badge>
      );
    } else {
      return (
        <Badge className="bg-red-600 text-white">
          <AlertCircle className="h-4 w-4 mr-1" /> {badText}
        </Badge>
      );
    }
  };

  const getOSIcon = (os) => {
    switch (os) {
      case "Windows":
        return "🪟";
      case "Darwin":
        return "🍎";
      case "Linux":
        return "🐧";
      default:
        return "💻";
    }
  };

  const renderUsageBar = (percent, color = "bg-blue-500") => {
    return (
      <div className="w-full">
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`${color} h-2.5 rounded-full`}
            style={{ width: `${percent}%` }}
          ></div>
        </div>
        <div className="text-xs text-gray-500 mt-1">{percent.toFixed(1)}%</div>
      </div>
    );
  };

  const filteredMachines = useMemo(() => {
    return machines.filter((machine) => {
      if (osFilter !== "all" && machine.os_platform !== osFilter) return false;

      const searchLower = searchTerm.toLowerCase();
      return (
        (machine.hostname || "").toLowerCase().includes(searchLower) ||
        (machine.username || "").toLowerCase().includes(searchLower) ||
        (machine.machine_id || "").toLowerCase().includes(searchLower) ||
        (machine.os_platform || "").toLowerCase().includes(searchLower) ||
        (machine.os_version || "").toLowerCase().includes(searchLower) ||
        (machine.disk_encryption ? "encrypted" : "unencrypted").includes(
          searchLower
        ) ||
        (machine.antivirus ? "active" : "inactive").includes(searchLower)
      );
    });
  }, [machines, searchTerm, osFilter]);

  const pageCount = Math.ceil(filteredMachines.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentItems = filteredMachines.slice(
    startIndex,
    startIndex + itemsPerPage
  );

  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0 || bytes == null) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(dm)} ${sizes[i]}`;
  };

  const avgCPUUsage = useMemo(() => {
    if (filteredMachines.length === 0) return 0;
    const total = filteredMachines.reduce(
      (sum, machine) => sum + (machine.cpu_usage || 0),
      0
    );
    return total / filteredMachines.length;
  }, [filteredMachines]);

  const avgMemoryUsage = useMemo(() => {
    if (filteredMachines.length === 0) return 0;
    const total = filteredMachines.reduce(
      (sum, machine) => sum + (machine.memory_usage || 0),
      0
    );
    return total / filteredMachines.length;
  }, [filteredMachines]);

  const avgDiskUsage = useMemo(() => {
    if (filteredMachines.length === 0) return 0;
    const total = filteredMachines.reduce(
      (sum, machine) => sum + (machine.disk_usage || 0),
      0
    );
    return total / filteredMachines.length;
  }, [filteredMachines]);

  return (
    <div className="min-h-screen bg-background p-4 sm:p-6">
      <div className="max-w-7xl mx-auto">
        <Card className="mb-6">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-2xl font-bold">
                  System Health Dashboard
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {lastUpdated
                    ? `Last updated: ${lastUpdated}`
                    : "Loading initial data..."}
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button onClick={fetchData} disabled={loading}>
                  <RefreshCw
                    className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
                  />
                  {loading ? "Loading..." : "Refresh Data"}
                </Button>

                <Button onClick={handleExport} variant="secondary">
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            <div className="flex flex-col md:flex-row gap-4 flex-wrap">
              <div className="relative w-full max-w-md">
                <Input
                  placeholder="Search machines..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div className="flex gap-2 flex-wrap">
                <Button
                  variant={osFilter === "all" ? "default" : "outline"}
                  onClick={() => setOsFilter("all")}
                >
                  All OS
                </Button>
                <Button
                  variant={osFilter === "Windows" ? "default" : "outline"}
                  onClick={() => setOsFilter("Windows")}
                >
                  🪟 Windows
                </Button>
                <Button
                  variant={osFilter === "Darwin" ? "default" : "outline"}
                  onClick={() => setOsFilter("Darwin")}
                >
                  🍎 macOS
                </Button>
                <Button
                  variant={osFilter === "Linux" ? "default" : "outline"}
                  onClick={() => setOsFilter("Linux")}
                >
                  🐧 Linux
                </Button>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm">Items per page:</span>
                <select
                  value={itemsPerPage}
                  onChange={(e) => setItemsPerPage(Number(e.target.value))}
                  className="border rounded p-1"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {error && (
          <Card className="mb-6 bg-destructive/10 border-destructive">
            <CardContent className="pt-6">
              <div className="text-center p-4">
                <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
                <h2 className="text-xl font-bold text-destructive mb-2">
                  Error Loading Data
                </h2>
                <p className="text-foreground mb-4">{error}</p>
                <Button onClick={fetchData} variant="destructive">
                  <RefreshCw className="h-4 w-4 mr-2" /> Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl font-semibold">
                System Status Overview
              </CardTitle>
              <div className="flex gap-2">
                <Badge variant="outline">
                  <Laptop className="h-4 w-4 mr-1" /> Machines:{" "}
                  {machines.length}
                </Badge>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full rounded-md" />
                ))}
              </div>
            ) : filteredMachines.length === 0 ? (
              <div className="text-center py-12">
                <Laptop className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium">
                  {searchTerm
                    ? "No matching machines found"
                    : "No machines reporting yet"}
                </h3>
                <p className="text-muted-foreground mt-2">
                  Install the system utility on target machines to start
                  receiving data
                </p>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Hostname</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>OS</TableHead>
                      <TableHead>
                        <Shield className="h-4 w-4 mr-1 inline" /> OS Updates
                      </TableHead>
                      <TableHead>Last Seen</TableHead>
                      <TableHead>
                        <Cpu className="h-4 w-4 mr-1 inline" /> CPU
                      </TableHead>
                      <TableHead>
                        <MemoryStick className="h-4 w-4 mr-1 inline" /> Memory
                      </TableHead>
                      <TableHead>
                        <HardDrive className="h-4 w-4 mr-1 inline" /> Disk
                      </TableHead>
                      <TableHead>
                        <Lock className="h-4 w-4 mr-1 inline" /> Encryption
                      </TableHead>
                      <TableHead>
                        <Shield className="h-4 w-4 mr-1 inline" /> Antivirus
                      </TableHead>
                      <TableHead>
                        <Moon className="h-4 w-4 mr-1 inline" /> Sleep
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {currentItems.map((machine) => (
                      <TableRow key={machine.machine_id}>
                        <TableCell className="font-medium">
                          <div>
                            <div>{machine.hostname || "Unknown"}</div>
                            <TooltipProvider delayDuration={0}>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <div className="text-xs text-muted-foreground truncate max-w-[150px] cursor-pointer">
                                    {machine.machine_id.substring(0, 8)}...
                                  </div>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="max-w-xs break-words">
                                    {machine.machine_id}
                                  </p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            <User className="h-4 w-4 mr-1 text-gray-500" />
                            <span>{machine.username || "Unknown"}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            <span className="mr-2 text-lg">
                              {getOSIcon(machine.os_platform)}
                            </span>
                            <div>
                              <div>{machine.os_platform}</div>
                              <div className="text-xs text-muted-foreground">
                                {machine.os_version}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(
                            !machine.os_updates,
                            "Updated",
                            "Update Available",
                            true
                          )}
                        </TableCell>
                        <TableCell>
                          {machine.last_seen
                            ? format(new Date(machine.last_seen * 1000), "PPpp")
                            : "Never"}
                        </TableCell>
                        <TableCell>
                          {renderUsageBar(
                            machine.cpu_usage || 0,
                            machine.cpu_usage > 80
                              ? "bg-red-500"
                              : machine.cpu_usage > 60
                              ? "bg-yellow-500"
                              : "bg-green-500"
                          )}
                          <div className="text-xs text-muted-foreground">
                            {machine.cpu_cores || 0} cores
                          </div>
                        </TableCell>
                        <TableCell>
                          {renderUsageBar(
                            machine.memory_usage || 0,
                            machine.memory_usage > 80
                              ? "bg-red-500"
                              : machine.memory_usage > 60
                              ? "bg-yellow-500"
                              : "bg-green-500"
                          )}
                          <div className="text-xs text-muted-foreground">
                            {machine.memory_mb
                              ? `${Math.round(machine.memory_mb / 1024)} GB`
                              : "N/A"}
                          </div>
                        </TableCell>
                        <TableCell>
                          <TooltipProvider delayDuration={0}>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="cursor-pointer w-full">
                                  {renderUsageBar(
                                    machine.disk_usage || 0,
                                    machine.disk_usage > 80
                                      ? "bg-red-500"
                                      : machine.disk_usage > 60
                                      ? "bg-yellow-500"
                                      : "bg-green-500"
                                  )}
                                </div>
                              </TooltipTrigger>
                              <TooltipContent className="max-w-lg">
                                <div className="grid gap-2">
                                  <div className="font-bold">
                                    Disk Information
                                  </div>
                                  {machine.disk_info &&
                                  machine.disk_info.length > 0 ? (
                                    <table className="min-w-full">
                                      <thead>
                                        <tr>
                                          <th className="text-left px-2">
                                            Mount
                                          </th>

                                          <th className="text-left px-2">
                                            Total
                                          </th>
                                          <th className="text-left px-2">
                                            Used
                                          </th>
                                          <th className="text-left px-2">
                                            Free
                                          </th>
                                          <th className="text-left px-2">
                                            Usage
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {machine.disk_info.map(
                                          (disk, index) => (
                                            <tr key={index}>
                                              <td className="px-2 py-1">
                                                {disk.mountpoint}
                                              </td>

                                              <td className="px-2 py-1">
                                                {formatBytes(disk.total)}
                                              </td>
                                              <td className="px-2 py-1">
                                                {formatBytes(disk.used)}
                                              </td>
                                              <td className="px-2 py-1">
                                                {formatBytes(disk.free)}
                                              </td>
                                              <td className="px-2 py-1">
                                                {disk.percent.toFixed(1)}%
                                              </td>
                                            </tr>
                                          )
                                        )}
                                      </tbody>
                                    </table>
                                  ) : (
                                    <div>Disk data not available</div>
                                  )}
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(
                            machine.disk_encryption,
                            "Encrypted",
                            "Unencrypted"
                          )}
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(
                            machine.antivirus,
                            "Active",
                            "Inactive"
                          )}
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(
                            machine.sleep_settings,
                            "≤10 min",
                            ">10 min"
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>

          <CardFooter>
            <div className="flex items-center justify-between w-full">
              <p className="text-sm text-muted-foreground">
                Showing {Math.min(startIndex + 1, filteredMachines.length)} to{" "}
                {Math.min(startIndex + itemsPerPage, filteredMachines.length)}{" "}
                of {filteredMachines.length} machines
              </p>

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm">
                  Page {currentPage} of {pageCount}
                </span>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() =>
                    setCurrentPage(Math.min(pageCount, currentPage + 1))
                  }
                  disabled={currentPage === pageCount || pageCount === 0}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setCurrentPage(pageCount)}
                  disabled={currentPage === pageCount || pageCount === 0}
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardFooter>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Encryption Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {machines.filter((m) => m.disk_encryption).length}/
                {machines.length}
              </div>
              <p className="text-xs text-muted-foreground">
                Machines with disk encryption
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">OS Updates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {machines.filter((m) => !m.os_updates).length}/{machines.length}
              </div>
              <p className="text-xs text-muted-foreground">
                Machines needing updates
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Antivirus</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {machines.filter((m) => m.antivirus).length}/{machines.length}
              </div>
              <p className="text-xs text-muted-foreground">
                Machines with active antivirus
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Sleep Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {machines.filter((m) => m.sleep_settings).length}/
                {machines.length}
              </div>
              <p className="text-xs text-muted-foreground">
                Machines with proper sleep settings
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <Cpu className="h-4 w-4 mr-2" /> CPU Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {avgCPUUsage.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                Average across all machines
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <MemoryStick className="h-4 w-4 mr-2" /> Memory Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {avgMemoryUsage.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                Average across all machines
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <HardDrive className="h-4 w-4 mr-2" /> Disk Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {avgDiskUsage.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                Average across all machines
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
